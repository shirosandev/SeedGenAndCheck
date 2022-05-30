from secrets import token_bytes
from coincurve import PublicKey
from sha3  import keccak_256
from web3 import Web3
import sqlite3
from rich import print as printc
from threading import Thread


infura_url = "" # Берем mainnet эфира от сюда -> https://infura.io (бесплатная регистрация)
w3 = Web3(Web3.HTTPProvider(infura_url))
bd_pool = []

def generate_eth():

    private_key = keccak_256(token_bytes(32)).digest()
    public_key = PublicKey.from_valid_secret(private_key).format(compressed=False)[1:]
    addr = keccak_256(public_key).digest()[-20:]
    return {
        "private_key" : private_key.hex(),
        "public_key" : public_key,
        "addr" : addr.hex()
    }



def bd_worker():
    connection = sqlite3.connect("db.db")
    cursor = connection.cursor()
    with connection:
        cursor.execute("CREATE TABLE IF NOT EXISTS wallets ('addr' VARCHAR, 'private' VARCHAR, 'balance' double)")
    while 1:
        for addr_info in bd_pool:
            bd_pool.remove(addr_info)
            if addr_info['ether_value'] == 0:
                continue
            with connection:
                cursor.execute(f"INSERT INTO wallets VALUES ('{addr_info['addr']}', '{addr_info['private_key']}', {addr_info['ether_value']})")


def worker():
    while 1:
        addr_info = generate_eth()
        check_sum = w3.toChecksumAddress(addr_info['addr'])
        balance = w3.eth.get_balance(check_sum)
        ether_value  = w3.fromWei(balance, 'ether')
        addr_info['ether_value'] = ether_value
        bd_pool.append(addr_info)
        if ether_value > 0:
            printc(f"[green] {ether_value} | 0x{addr_info['addr']} [/green]")
        else:
            printc(f"[red] {ether_value} | 0x{addr_info['addr']} [/red]")
            #print(f"{ether_value} | 0x{addr_info['addr']}")


Thread(target=bd_worker).start()

threads = []
for _ in range(0,20):
    thread = Thread(target=worker)
    thread.start()
    threads.append(thread)

for worker in threads:
    worker.join()

