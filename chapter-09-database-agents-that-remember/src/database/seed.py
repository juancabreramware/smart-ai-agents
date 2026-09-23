from __future__ import annotations
import sqlite3
from pathlib import Path

def build(path: Path, schema_path: Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): path.unlink()
    c=sqlite3.connect(path); c.executescript(schema_path.read_text())
    c.executemany('INSERT INTO customers VALUES (?,?)',[(f'C{i:03}','Customer '+str(i)) for i in range(1,7)])
    c.executemany('INSERT INTO products VALUES (?,?,?)',[(f'SKU{i:03}',f'Product {i}',10+i%4) for i in range(1,13)])
    c.executemany('INSERT INTO suppliers VALUES (?,?)',[(f'S{i:03}',f'Supplier {i}') for i in range(1,5)])
    orders=[]; items=[]
    for i in range(1,49):
        oid=f'O{i:04}'; cid=f'C{(i%6)+1:03}'; status=['OPEN','SHIPPED','CLOSED'][i%3]; date=f'2026-{1+(i%6):02}-{1+(i%27):02}'
        orders.append((oid,cid,status,date))
        for j in (1,2):
            qty=1+(i+j)%5; unit=10+(i%9)*3+j; ext=qty*unit; disc=round(ext*(0.05 if i%4==0 else 0),2); items.append((oid,f'SKU{((i+j)%12)+1:03}',qty,unit,ext,disc,ext-disc))
    c.executemany('INSERT INTO orders VALUES (?,?,?,?)',orders); c.executemany('INSERT INTO order_items VALUES (?,?,?,?,?,?,?)',items)
    inv=[]; pol=[]
    for wh in ['W1','W2']:
        for i in range(1,13): inv.append((wh,f'SKU{i:03}',(i*3+(1 if wh=='W2' else 0))%20)); pol.append((wh,f'SKU{i:03}',8+(i%7)+(2 if wh=='W2' else 0)))
    c.executemany('INSERT INTO inventory_balances VALUES (?,?,?)',inv); c.executemany('INSERT INTO warehouse_inventory_policy VALUES (?,?,?)',pol)
    pos=[]; pois=[]
    for i in range(1,25):
        po=f'PO{i:03}'; sid=f'S{(i%4)+1:03}'; date=f'2026-{1+(i%6):02}-{2+(i%25):02}'; total=100+i*11
        pos.append((po,sid,date,total)); pois += [(po,'SKU001',total*.45,total*.40),(po,'SKU002',total*.55,total*.48)]
    c.executemany('INSERT INTO purchase_orders VALUES (?,?,?,?)',pos); c.executemany('INSERT INTO purchase_order_items VALUES (?,?,?,?)',pois)
    ships=[]
    for i in range(1,31):
        d=1+(i%20); promised=d+4; commitment=d+(3 if i%4==0 else 5); delivered=d+(6 if i%3==0 else 3)
        ships.append((f'SH{i:03}',f'O{i:04}',f'2026-04-{d:02}',f'2026-04-{min(promised,28):02}',f'2026-04-{min(commitment,28):02}',f'2026-04-{min(delivered,28):02}'))
    c.executemany('INSERT INTO shipments VALUES (?,?,?,?,?,?)',ships)
    invoices=[]
    for i in range(1,25): invoices.append((f'I{i:03}',f'2026-0{1+(i%4)}-{1+(i%25):02}',f'2026-0{2+(i%4)}-{1+(i%25):02}',200+i*17, (200+i*17) if i%4==0 else i*10))
    c.executemany('INSERT INTO invoices VALUES (?,?,?,?,?)',invoices)
    c.commit(); c.close()
