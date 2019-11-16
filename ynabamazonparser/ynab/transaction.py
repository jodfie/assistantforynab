from ynab_sdk.api.models.responses.transactions import Transaction as _Transaction
import datetime
from dataclasses import dataclass


@dataclass
class Transaction(_Transaction):
    date_format = '%Y-%m-%d'

    def __init__(self, t):
        self._date = t.date
        self._amount = t.amount
        super().__init__(**t.__dict__)

    @property
    def amount(self):
        return self._amount

    @property
    def date(self):
        return self._date

    # These allow us to not think about milliunits
    @amount.getter
    def amount(self):
        return abs(self._amount / 1000)

    @amount.setter
    def amount(self, a):
        self._amount = abs(a) * (1 if self._amount > 0 else -1)

    def is_outflow(self):
        return self._amount < 0

    def is_inflow(self):
        return self._amount > 0

    @date.getter
    def date(self):
        return datetime.datetime.strptime(self._date, Transaction.date_format)

    @date.setter
    def date(self, d):
        if isinstance(d, datetime.datetime):
            self._date = datetime.strftime(d, Transaction.date_format)
        else:
            # make sure it's a valid format
            datetime.datetime.strptime(d, Transaction.date_format)
            self._date = d

    def to_parent(self):
        d = self.__dict__.copy()
        d['amount'] = self._amount
        d['date'] = self._date
        del d['_amount']
        del d['_date']
        return _Transaction(**d)

    def __repr__(self):
        str_fields = self.id, self._date, '$' + str(self.amount)
        return ' | '.join(map(str, str_fields))
