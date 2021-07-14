import os
import ssl
import ldap3
from ldap3 import Tls


class LDAP:
    def __init__(self, *args, **kwargs):
        # TODO add some default values
        server = os.getenv('LDAP_SERVER','')
        username = os.getenv('LDAP_USER','')
        password = os.getenv('LDAP_PASSWORD','')
        tls = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
        self.server = ldap3.Server(server, port=636, use_ssl=True, tls=tls)
        self.connection = ldap3.Connection(self.server, username, password)
        print('LDAP connection...', self.connection)

    def search(self, field, text):
        search_dir = os.getenv('LDAP_DIRECTORY','')
        attributes = ['telephoneNumber', 'CN', 'mail', 'mobile', 'pager', 'thumbnailPhoto']
        search_string = '(&(' + field + '='
        for word in text.split():
            search_string += '*' + word + '*'
        search_string += '))'

        self.connection.bind()
        if not self.connection.search(search_dir, search_string, attributes=attributes):
            print('Exiting directory... connection not established.')
            return {}

        results = {}
        for result in self.connection.entries:
            name = result.cn.value
            results[name] = {}
            if result.telephoneNumber.value is None:
                results[name]['phone'] = ''
            else:
                results[name]['phone'] = result.telephoneNumber.value.replace(' ', '')
            if result.mobile.value is None:
                results[name]['mobile'] = ''
            else:
                results[name]['mobile'] = result.mobile.value.replace(' ', '')
            if result.pager.value is None:
                results[name]['pager'] = ''
            else:
                results[name]['pager'] = result.pager.value.replace(' ', '')
            if result.mail.value is None:
                results[name]['email'] = ''
            else:
                results[name]['email'] = result.mail.value

            if result.thumbnailPhoto.value is None:
                results[name]['photo'] = ''
            else:
                results[name]['photo'] = result.thumbnailPhoto.value
        self.connection.unbind()
        print('Exiting directory... Data found.')
        return results
