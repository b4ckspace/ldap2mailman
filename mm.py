#!/usr/bin/python3
"""Wrapper script to work around mailman cli limitations in debian buster."""

# pylint: disable=import-error
from mailman.app.membership import add_member, delete_member
from mailman.core.initialize import initialize
from mailman.database.transaction import transactional
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.member import DeliveryMode
from mailman.interfaces.subscriptions import RequestRecord
from zope.component import getUtility


# initialize on import
initialize()


class ListManager:
    """Helper class to manage a mailman3 mailinglist."""
    def __init__(self, mailinglist):
        self.list = getUtility(IListManager).get(mailinglist)

    @transactional
    def add(self, email):
        """Add email to mailinglist."""
        add_member(self.list, RequestRecord(email, '', DeliveryMode.regular,
                                            self.list.preferred_language.code))

    @transactional
    def delete(self, email):
        """Remove email from mailinglist."""
        delete_member(self.list, email)

    @property
    def members(self):
        """List of members on the mailinglist."""
        return [a.email for a in self.list.members.addresses]
