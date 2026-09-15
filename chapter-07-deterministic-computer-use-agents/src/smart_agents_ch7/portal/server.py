from __future__ import annotations

from contextlib import contextmanager
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import html
import threading
import urllib.parse
from typing import Iterator

from .state import PortalState


def _page(title: str, body: str) -> bytes:
    doc = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>{html.escape(title)}</title>
<style>
body{{font-family:Arial,sans-serif;max-width:820px;margin:36px auto;padding:0 20px;color:#102a43}}
label{{display:block;margin:10px 0 4px}} input,select{{padding:7px;width:360px}}
button{{margin-top:14px;padding:8px 14px}} .ok{{padding:12px;background:#e8f7ef;border-left:4px solid #159957}}
.err{{padding:12px;background:#fff0f0;border-left:4px solid #d7263d}}
</style></head><body><h1>{html.escape(title)}</h1>{body}</body></html>"""
    return doc.encode("utf-8")


class PortalHandler(BaseHTTPRequestHandler):
    state: PortalState

    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, body: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length).decode("utf-8")
        parsed = urllib.parse.parse_qs(raw, keep_blank_values=True)
        return {k: v[-1] if v else "" for k, v in parsed.items()}

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        v = self.state.ui_version
        if path == "/":
            self._send(_page("HarborPoint Operations Portal", f"<p data-testid='portal-version'>{v}</p>"))
            return
        if path == "/orders/status":
            self._send(_page("Order Status", """
<form method='post'>
<label>Order ID</label><input data-testid='order-id' name='order_id'>
<button data-testid='order-status-submit'>Lookup</button>
</form>""")); return
        if path == "/customers/contact":
            self._send(_page("Customer Contact", """
<form method='post'>
<label>Customer ID</label><input data-testid='customer-id' name='customer_id'>
<label>Email</label><input data-testid='customer-email' name='email'>
<label>Phone</label><input data-testid='customer-phone' name='phone'>
<button data-testid='customer-submit'>Save</button>
</form>""")); return
        if path == "/shipping/update" and v == "V1":
            self._send(_page("Shipping Instructions", """
<form method='post'>
<label>Order ID</label><input data-testid='shipping-order-id' name='order_id'>
<label>Delivery Window</label><input data-testid='delivery-window' name='delivery_window'>
<label>Instructions</label><input data-testid='shipping-instructions' name='instructions'>
<button data-testid='shipping-submit'>Save</button>
</form>""")); return
        if path == "/shipping/details" and v == "V2":
            self._send(_page("Shipment Details", """
<form method='post'>
<label>Order ID</label><input data-testid='shipment-order-id' name='order_id'>
<label>Delivery Window</label><input data-testid='shipment-window' name='delivery_window'>
<label>Notes</label><input data-testid='shipment-notes' name='instructions'>
<button data-testid='shipment-save'>Save shipment details</button>
</form>""")); return
        if path == "/billing/credit":
            if v == "V1":
                body = """
<form method='post'>
<label>Customer ID</label><input data-testid='billing-customer-id' name='customer_id'>
<label>Amount (USD)</label><input data-testid='billing-amount' name='amount'>
<button data-testid='billing-submit'>Apply credit</button>
</form>"""
            else:
                body = """
<form method='post'>
<label>Customer ID</label><input data-testid='billing-customer-id' name='customer_id'>
<label>Amount (cents)</label><input data-testid='billing-amount-cents' name='amount_cents'>
<label>Reason code</label><select data-testid='billing-reason-code' name='reason_code'>
<option value='SERVICE'>SERVICE</option><option value='SHIPPING'>SHIPPING</option><option value='GOODWILL'>GOODWILL</option></select>
<label>Approval code (required over $100)</label><input data-testid='billing-approval-code' name='approval_code'>
<button data-testid='billing-submit-v2'>Apply credit</button>
</form>"""
            self._send(_page("Apply Credit", body)); return
        if path == "/returns/create":
            if v == "V1":
                body = """
<form method='post'>
<label>Order ID</label><input data-testid='return-order-id' name='order_id'>
<label>Item SKU</label><input data-testid='return-item-sku' name='item_sku'>
<label>Reason</label><select data-testid='return-reason' name='reason'>
<option value='DAMAGED'>DAMAGED</option><option value='WRONG_ITEM'>WRONG_ITEM</option><option value='OTHER'>OTHER</option></select>
<button data-testid='return-submit'>Create RMA</button>
</form>"""
            else:
                body = """
<form method='post' action='/returns/reason'>
<label>Order ID</label><input data-testid='return-order-id-v2' name='order_id'>
<label>Item SKU</label><input data-testid='return-item-sku-v2' name='item_sku'>
<button data-testid='return-next'>Next</button>
</form>"""
            self._send(_page("Create Return Authorization", body)); return
        if path == "/inventory/reserve":
            if v == "V1":
                body = """
<form method='post'>
<label>SKU</label><input data-testid='inventory-sku' name='sku'>
<label>Warehouse</label><input data-testid='warehouse-id' name='location'>
<label>Quantity</label><input data-testid='inventory-quantity' name='quantity'>
<button data-testid='inventory-submit'>Reserve</button>
</form>"""
            else:
                body = """
<form method='post' action='/inventory/confirm'>
<label>SKU</label><input data-testid='inventory-sku-v2' name='sku'>
<label>Location</label><input data-testid='location-id' name='location'>
<label>Quantity</label><input data-testid='inventory-quantity-v2' name='quantity'>
<button data-testid='inventory-review'>Review reservation</button>
</form>"""
            self._send(_page("Reserve Inventory", body)); return

        self._send(_page("Not Found", "<p class='err'>This route does not exist in the active UI contract.</p>"), HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        data = self._form()
        v = self.state.ui_version

        if path == "/orders/status":
            order_id = data.get("order_id", "")
            status = self.state.orders.get(order_id, {}).get("status")
            if status is None:
                self._send(_page("Order Status", "<p class='err'>Unknown order</p>"), 400); return
            self._send(_page("Order Status", f"<p class='ok' data-testid='order-status-result'>{html.escape(status)}</p>")); return

        if path == "/customers/contact":
            cid = data.get("customer_id", "")
            if cid not in self.state.customers:
                self._send(_page("Customer Contact", "<p class='err'>Unknown customer</p>"), 400); return
            self.state.customers[cid] = {"email": data.get("email", ""), "phone": data.get("phone", "")}
            self._send(_page("Customer Contact", "<p class='ok' data-testid='success'>Contact updated</p>")); return

        if path == "/shipping/update" and v == "V1":
            oid = data.get("order_id", "")
            self.state.shipping[oid] = {"delivery_window": data.get("delivery_window", ""), "instructions": data.get("instructions", "")}
            self._send(_page("Shipping Instructions", "<p class='ok' data-testid='success'>Shipping updated</p>")); return

        if path == "/shipping/details" and v == "V2":
            oid = data.get("order_id", "")
            self.state.shipping[oid] = {"delivery_window": data.get("delivery_window", ""), "instructions": data.get("instructions", "")}
            self._send(_page("Shipment Details", "<p class='ok' data-testid='success'>Shipment updated</p>")); return

        if path == "/billing/credit":
            cid = data.get("customer_id", "")
            if cid not in self.state.customers:
                self._send(_page("Apply Credit", "<p class='err'>Unknown customer</p>"), 400); return
            if v == "V1":
                try: amount = float(data.get("amount", "0"))
                except ValueError: amount = -1
                if amount <= 0:
                    self._send(_page("Apply Credit", "<p class='err'>Invalid amount</p>"), 400); return
                record = {"customer_id": cid, "amount": round(amount,2), "reason_code": None, "approval_code": None}
            else:
                try: cents = int(data.get("amount_cents", "0"))
                except ValueError: cents = -1
                reason = data.get("reason_code", "")
                approval = data.get("approval_code", "")
                if cents <= 0 or not reason:
                    self._send(_page("Apply Credit", "<p class='err'>Invalid credit</p>"), 400); return
                if cents > 10000 and not approval:
                    self._send(_page("Apply Credit", "<p class='err'>Approval required</p>"), 400); return
                record = {"customer_id": cid, "amount": round(cents/100,2), "reason_code": reason, "approval_code": approval or None}
            self.state.credits.append(record)
            self._send(_page("Apply Credit", "<p class='ok' data-testid='success'>Credit applied</p>")); return

        if path == "/returns/create" and v == "V1":
            rec = {"order_id": data.get("order_id", ""), "item_sku": data.get("item_sku", ""), "reason": data.get("reason", "")}
            self.state.returns.append(rec)
            self._send(_page("Create Return Authorization", "<p class='ok' data-testid='success'>RMA created</p>")); return

        if path == "/returns/reason" and v == "V2":
            oid = data.get("order_id", ""); sku = data.get("item_sku", "")
            body = f"""
<form method='post' action='/returns/complete'>
<input type='hidden' name='order_id' value='{html.escape(oid)}'>
<input type='hidden' name='item_sku' value='{html.escape(sku)}'>
<label>Reason</label><select data-testid='return-reason-v2' name='reason'>
<option value='DAMAGED'>DAMAGED</option><option value='WRONG_ITEM'>WRONG_ITEM</option><option value='OTHER'>OTHER</option></select>
<button data-testid='return-submit-v2'>Create RMA</button>
</form>"""
            self._send(_page("Return Reason", body)); return

        if path == "/returns/complete" and v == "V2":
            rec = {"order_id": data.get("order_id", ""), "item_sku": data.get("item_sku", ""), "reason": data.get("reason", "")}
            self.state.returns.append(rec)
            self._send(_page("Create Return Authorization", "<p class='ok' data-testid='success'>RMA created</p>")); return

        if path == "/inventory/reserve" and v == "V1":
            rec = {"sku": data.get("sku", ""), "location": data.get("location", ""), "quantity": int(data.get("quantity", "0") or 0)}
            self.state.reservations.append(rec)
            self._send(_page("Reserve Inventory", "<p class='ok' data-testid='success'>Inventory reserved</p>")); return

        if path == "/inventory/confirm" and v == "V2":
            body = f"""
<form method='post' action='/inventory/complete'>
<input type='hidden' name='sku' value='{html.escape(data.get('sku',''))}'>
<input type='hidden' name='location' value='{html.escape(data.get('location',''))}'>
<input type='hidden' name='quantity' value='{html.escape(data.get('quantity','0'))}'>
<p>Confirm reservation</p><button data-testid='inventory-confirm'>Confirm</button>
</form>"""
            self._send(_page("Confirm Reservation", body)); return

        if path == "/inventory/complete" and v == "V2":
            rec = {"sku": data.get("sku", ""), "location": data.get("location", ""), "quantity": int(data.get("quantity", "0") or 0)}
            self.state.reservations.append(rec)
            self._send(_page("Reserve Inventory", "<p class='ok' data-testid='success'>Inventory reserved</p>")); return

        self._send(_page("Not Found", "<p class='err'>Unsupported action</p>"), HTTPStatus.NOT_FOUND)


class PortalHarness:
    def __init__(self, state: PortalState | None = None):
        self.state = state or PortalState()
        handler = type("BoundPortalHandler", (PortalHandler,), {"state": self.state})
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self) -> "PortalHarness":
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
