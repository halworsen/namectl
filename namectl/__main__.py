import argparse
from namectl.controller import controller_loop

if __name__ == '__main__':
    argparser = argparse.ArgumentParser('namectl')
    argparser.add_argument('-c', '--config', type=str, help='Path to DNS config', required=True)
    argparser.add_argument('-p', '--loop-period', type=int, help='How often attempt record reconciliation', default=300)
    args = argparser.parse_args()

    controller_loop(args)
