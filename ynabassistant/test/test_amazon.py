import ynabassistant as ya


def main():
    ya.test.test_data_setup.main()
    a = ya.Assistant
    a.download_all_ynab()
    a.load_amazon_data()
    a.update_amazon_transactions()
    a.update_ynab()


if __name__ == '__main__':
    main()