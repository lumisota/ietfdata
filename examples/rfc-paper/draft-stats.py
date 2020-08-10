# Copyright (C) 2020 University of Glasgow
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import sys
import os
import pickle
import pathlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ietfdata.datatracker import *
from ietfdata.rfcindex    import *

dt = DataTracker(cache_dir=Path("cache"))
rfc_index = RFCIndex()
rfc_to_draft = {}

replaces = dt.relationship_type(RelationshipTypeURI("/api/v1/name/docrelationshipname/replaces/"))

def find_replaced(doc):
    replaced_docs = list(dt.related_documents(source=doc, relationship_type=replaces))
    replaced_docs = [dt.document_alias(replaced_doc.target) for replaced_doc in replaced_docs]
    for replaced_doc in replaced_docs:
        other_replaced_docs = find_replaced(replaced_doc)
        for other_replaced_doc in other_replaced_docs:
            if other_replaced_doc not in replaced_docs:
                replaced_docs.append(other_replaced_doc)
    return replaced_docs

# fetch RFCs through the end of 2019

rfcs = rfc_index.rfcs(since="2019-01", until="2019-12")

if not pathlib.Path("rfc_data.pickle").exists():
    for rfc in rfcs:
        doc = dt.document_from_rfc(rfc.doc_id)
        rfc_to_draft[rfc.doc_id] = []
        print(rfc.doc_id)
        if doc is not None:
            print("^", doc.name)
            rfc_to_draft[rfc.doc_id].append(doc.name)

    with open('rfc_data.pickle', 'wb') as f:
        pickle.dump(rfc_to_draft, f, pickle.HIGHEST_PROTOCOL)
else:
    with open('rfc_data.pickle', 'rb') as f:
        rfc_to_draft = pickle.load(f)

for rfc in rfc_to_draft:
    print(rfc)
    if len(rfc_to_draft[rfc]) == 1 and rfc_to_draft[rfc][0][:6] == "draft-":
        doc = dt.document_from_draft(rfc_to_draft[rfc][0])
        if doc is not None:
            print("...", rfc_to_draft[rfc] + [doc.name for doc in find_replaced(doc)])
