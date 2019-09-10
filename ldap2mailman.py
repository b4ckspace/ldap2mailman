#!/usr/bin/python3
"""Sync ldap users to mailman.

This script is used to sync ldap users periodically to mailman.
A notification mail will be sent.

Edit the gobal variables to match your environment.
"""

import smtplib
from email.message import EmailMessage
import ldap3

import mm
import config


def main():
    """Sync users."""
    ldap_addrs = []
    ldap_lookup = {}
    ldap_server = ldap3.Server(config.LDAP_URI)
    with ldap3.Connection(ldap_server, *config.LDAP_AUTH) as conn:
        conn.start_tls()
        conn.search(config.LDAP_SEARCH, search_filter=config.LDAP_SEARCH_FILTER,
                    attributes=[config.LDAP_MAIL_ATTR, config.LDAP_NAME_ATTR])
        for member in conn.entries:
            mail = member.__getitem__(config.LDAP_MAIL_ATTR)
            if mail:
                mail = str(mail).lower()
                ldap_addrs.append(mail)
                ldap_lookup[mail] = member

    list_manager = mm.ListManager(config.MLIST)
    mm3_addrs = list_manager.members

    for user in (user for user in ldap_addrs if user not in mm3_addrs):
        member = ldap_lookup[user]
        username = member.__getitem__(config.LDAP_NAME_ATTR)
        list_manager.add(user)
        with smtplib.SMTP(config.MAIL_SERVER) as s:  # pylint: disable=invalid-name
            s.ehlo()
            s.starttls()
            msg = EmailMessage()
            msg.set_content(config.MAIL_BODY.format(name=username))
            msg['To'] = config.WELCOME_TO
            msg['From'] = config.WELCOME_FROM
            msg['Subject'] = config.WELCOME_SUBJECT
            s.send_message(msg)

    for user in (user for user in mm3_addrs if user not in ldap_addrs):
        list_manager.delete(user)


if __name__ == '__main__':
    main()
