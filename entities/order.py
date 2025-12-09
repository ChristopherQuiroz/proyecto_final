from datetime import datetime
from bson import ObjectId
from entities.orderDetail import OrderDetail

class Order:
    STATUSES = ["pendiente", "pagado", "cancelado", "aceptado"]

    def __init__(self, customer_id, employee_id=None, date=None, status="pendiente", total=0.0, details=None, created_in_person=False):
        self.customer_id = ObjectId(customer_id)                # referencia a User._id o Cliente._id
        self.employee_id = ObjectId(employee_id) if employee_id else None  # empleado que acepta el pedido
        self.date = date if date else datetime.utcnow()
        self.status = status if status in self.STATUSES else "pendiente"
        self.total = total
        self.details = details if details else []              # lista de OrderDetail
        self.created_in_person = created_in_person             # True si se creó presencialmente

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "employee_id": self.employee_id,
            "date": self.date,
            "status": self.status,
            "total": self.total,
            "details": [detail.to_dict() for detail in self.details],
            "created_in_person": self.created_in_person
        }

    @staticmethod
    def from_dict(data):
        details = [OrderDetail.from_dict(d) for d in data.get("details", [])]
        return Order(
            customer_id=data.get("customer_id"),
            employee_id=data.get("employee_id"),
            date=data.get("date"),
            status=data.get("status", "pendiente"),
            total=data.get("total", 0.0),
            details=details,
            created_in_person=data.get("created_in_person", False)
        )
