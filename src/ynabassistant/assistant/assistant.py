import collections
import utils
import amazon
import backup
import ynab


class Assistant:

    accounts = utils.Cache()
    transactions = utils.TransactionCache(accounts)
    categories = utils.Cache()
    category_groups = utils.Cache()
    payees = utils.Cache()

    orders = collections.defaultdict(list)
    items = {}

    def load_amazon_data():
        utils.log_info('Loading Amazon')
        Assistant.orders = amazon.downloader.load('orders')  # by order.id
        Assistant.items = amazon.downloader.load('items')  # grouped by order.id
        utils.log_info(utils.separator)

    def load_ynab(accounts=False, transactions=False, categories=False, payees=False, local=False):
        assert accounts or transactions or categories or payees
        source = backup.local if local else ynab.api_client

        # Need accounts to validate transactions pending deleted account bug fix
        if transactions or accounts:
            Assistant.accounts.store(source.get_accounts())
            if accounts:
                utils.log_info('Found %s accounts' % len(Assistant.accounts))

        if transactions:
            Assistant.transactions.store(source.get_transactions())
            utils.log_info('Found %s transactions' % len(Assistant.transactions))

        if categories:
            Assistant.category_groups.store(source.get_category_groups())
            utils.log_info('Found %s category groups' % len(Assistant.category_groups))
            Assistant.categories.store(c for g in Assistant.category_groups for c in g.categories)
            utils.log_info('Found %s categories' % len(Assistant.categories))

        if payees:
            Assistant.payees.store(source.get_payees())
            utils.log_info('Found %s payees' % len(Assistant.payees))

        utils.log_info(utils.separator)

    def download_ynab(accounts=False, transactions=False, categories=False, payees=False):
        utils.log_info('Downloading YNAB')
        Assistant.load_ynab(accounts, transactions, categories, payees, local=False)

    def restore_ynab(accounts=False, transactions=False, categories=False, payees=False):
        utils.log_info('Restoring YNAB')
        Assistant.load_ynab(accounts, transactions, categories, payees, local=True)

    def download_all_ynab():
        Assistant.download_ynab(True, True, True, True)

    def restore_all_ynab():
        Assistant.restore_ynab(True, True, True, True)

    def update_amazon_transactions():
        utils.log_info('Matching Amazon orders to YNAB transactions')
        potential_amazon_transactions = amazon.get_eligible_transactions(Assistant.transactions)
        orders_by_transaction_id = amazon.match.match_all(potential_amazon_transactions, Assistant.orders)
        for t_id, order in orders_by_transaction_id.items():
            order = orders_by_transaction_id[t_id]
            i = Assistant.items[order.id]
            assert i
            t = Assistant.transactions.get(t_id)
            amazon.annotate(t, order, i)
            # ynab.queue_update(t, Assistant.payees, Assistant.categories)
            ynab.queue_update(t)
        utils.log_info(utils.separator)

    def update_ynab():
        ynab.do()
