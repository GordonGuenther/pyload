# -*- coding: utf-8 -*-

import re

from urllib import unquote
from urlparse import urlparse

from pyload.network.HTTPRequest import BadHeader
from pyload.plugins.base.Hoster import Hoster
from pyload.utils import html_unescape, remove_chars


class BasePlugin(Hoster):
    __name__    = "BasePlugin"
    __type__    = "hoster"
    __version__ = "0.20"

    __pattern__ = r'^unmatchable$'

    __description__ = """Base Plugin when any other didnt fit"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True


    def process(self, pyfile):
        """main function"""

        #: debug part, for api exerciser
        if pyfile.url.startswith("DEBUG_API"):
            self.multiDL = False
            return

        if pyfile.url.startswith("http"):

            try:
                self.downloadFile(pyfile)
            except BadHeader, e:
                if e.code in (401, 403):
                    self.logDebug("Auth required")

                    account = self.core.accountManager.getAccountPlugin('Http')
                    servers = [x['login'] for x in account.getAllAccounts()]
                    server = urlparse(pyfile.url).netloc

                    if server in servers:
                        self.logDebug("Logging on to %s" % server)
                        self.req.addAuth(account.accounts[server]['password'])
                    else:
                        for pwd in pyfile.package().password.splitlines():
                            if ":" in pwd:
                                self.req.addAuth(pwd.strip())
                                break
                        else:
                            self.fail(_("Authorization required (username:password)"))

                    self.downloadFile(pyfile)
                else:
                    raise

        else:
            self.fail(_("No Plugin matched and not a downloadable url"))


    def downloadFile(self, pyfile):
        url = pyfile.url

        for _i in xrange(5):
            header = self.load(url, just_header=True)

            # self.load does not raise a BadHeader on 404 responses, do it here
            if 'code' in header and header['code'] == 404:
                raise BadHeader(404)

            if 'location' in header:
                self.logDebug("Location: " + header['location'])
                base = re.match(r'https?://[^/]+', url).group(0)
                if header['location'].startswith("http"):
                    url = header['location']
                elif header['location'].startswith("/"):
                    url = base + unquote(header['location'])
                else:
                    url = '%s/%s' % (base, unquote(header['location']))
            else:
                break

        name = html_unescape(unquote(urlparse(url).path.split("/")[-1]))

        if 'content-disposition' in header:
            self.logDebug("Content-Disposition: " + header['content-disposition'])
            m = re.search("filename(?P<type>=|\*=(?P<enc>.+)'')(?P<name>.*)", header['content-disposition'])
            if m:
                disp = m.groupdict()
                self.logDebug(disp)
                if not disp['enc']:
                    disp['enc'] = 'utf-8'
                name = remove_chars(disp['name'], "\"';").strip()
                name = unicode(unquote(name), disp['enc'])

        if not name:
            name = url
        pyfile.name = name
        self.logDebug("Filename: %s" % pyfile.name)
        self.download(url, disposition=True)