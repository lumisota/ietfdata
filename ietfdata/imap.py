# Copyright (C) 2017-2020 University of Glasgow
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

import glob
import email

from email.message import Message
from imapclient    import IMAPClient
from pathlib       import Path
from typing        import Optional, List, Dict

# =================================================================================================================================
# A class to represent the IETF IMAP client:

class IMAP:
    """
    A class for interacting with the IETF IMAP server.
    """
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Parameters:
            cache_dir      -- If set, use this directory as a cache for messages
        """
        self.cache_dir = cache_dir
        self.server   = IMAPClient("imap.ietf.org", use_uid=True, ssl=False)
        self.server.login("anonymous", "anonymous@imap.ietf.org")


    def _cached_message_paths(self, folder_name: str) -> List[int]:
        if self.cache_dir is not None:
            return [eml_file for eml_file in glob.glob(str(Path(self.cache_dir, "imap", folder_name)) + "/*.eml")]
        else:
            return []

    def _highest_uid_seen(self, cached_message_paths: List[str]):
        return max([int(eml_file[eml_file.rfind('/')+1:-4]) for eml_file in cached_message_paths], default=0)

    def _fetch_all_folder(self, folder_name: str) -> List[Message]:
        self.server.select_folder(folder_name, readonly=True)
        messages = []
        for cached_message_path in self._cached_message_paths(folder_name):
            with open(cached_message_path, "rb") as cached_message_file:
                message = email.message_from_bytes(cached_message_file.read())
            messages.append(message)
        highest_uid_seen = self._highest_uid_seen(self._cached_message_paths(folder_name))
        self.server.select_folder(folder_name, readonly=True)
        for uid, message_data in self.server.fetch("%d:*" % (highest_uid_seen+1), 'RFC822').items():
             message = email.message_from_bytes(message_data[b'RFC822'])
             if self.cache_dir is not None:
                 cache_filepath = Path(self.cache_dir, "imap", folder_name, str(uid) + ".eml")
                 cache_filepath.parent.mkdir(parents=True, exist_ok=True)
                 with open(cache_filepath, "wb") as cache_file:
                     cache_file.write(message_data[b'RFC822'])
             messages.append(message)
        return messages

    def _fetch_all(self) -> Dict[str, Message]:
        messages = {}
        for (flags, delimiter, name) in self.server.list_folders():
            if b"\\Noselect" not in flags:
                messages[name] = self._fetch_all_folder(name)
        return messages


imap = IMAP(Path("cache"))
imap._fetch_all()
