#!/usr/bin/python3
"""Sync ldap users to mailman.

This script is used to sync ldap users periodically to mailman.
A notification mail will be sent.

Edit the gobal variables to match your environment.
"""

from collections import namedtuple
from email.message import EmailMessage
import smtplib

import ldap3

import mm
import config


def main():
    """Sync users."""
    Member = namedtuple("Member", ["name", "email", "altmail", "uid_number"])

    ldap_addrs = []
    ldap_lookup = {}
    ldap_server = ldap3.Server(config.LDAP_URI)
    with ldap3.Connection(ldap_server, *config.LDAP_AUTH) as conn:
        conn.search(config.LDAP_SEARCH, search_filter=config.LDAP_SEARCH_FILTER,
                    attributes=[config.LDAP_UIDNUMBER_ATTR, config.LDAP_MAIL_ATTR,
                                config.LDAP_ALTMAIL_ATTR, config.LDAP_NAME_ATTR])
        for member in conn.entries:
            name = member.__getitem__(config.LDAP_NAME_ATTR)
            mail = member.__getitem__(config.LDAP_MAIL_ATTR)
            altmail = member.__getitem__(config.LDAP_ALTMAIL_ATTR)
            uid_number = member.__getitem__(config.LDAP_UIDNUMBER_ATTR)
            if mail:
                mail = str(mail).lower()
                ldap_addrs.append(mail)
                ldap_lookup[mail] = Member(name, mail, altmail, uid_number)

    list_manager = mm.ListManager(config.MLIST)
    mm3_addrs = list_manager.members

    ldap_addrs.remove("rechnungen@hackerspace-bamberg.de")

    for email in (email for email in ldap_addrs if email not in mm3_addrs):
        member = ldap_lookup[email]
        with smtplib.SMTP(config.MAIL_SERVER) as s:  # pylint: disable=invalid-name
            s.ehlo()
            s.starttls()
            msg = EmailMessage()
            msg.set_content(config.MAIL_BODY.format(name=member.name))
            msg['To'] = config.WELCOME_TO
            msg['Bcc'] = Member.altmail
            msg['From'] = config.WELCOME_FROM
            msg['Subject'] = config.WELCOME_SUBJECT
            s.send_message(msg, to_addrs=[config.WELCOME_TO])
        list_manager.add(member.email)

    for email in (email for email in mm3_addrs if email not in ldap_addrs):
        list_manager.delete(email)

    for mlist in config.MORE_MLISTS:
        list_manager = mm.ListManager(mlist)
        list_members = list_manager.members
        for email in (email for email in ldap_addrs if email not in list_members):
            list_manager.add(email)


if __name__ == '__main__':
    main()
