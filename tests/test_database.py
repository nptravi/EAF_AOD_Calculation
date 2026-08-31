from sqlalchemy.exc import IntegrityError

from app.database.queries import get_oxidation_master

oxidations = get_oxidation_master()
oxidation_rates = {
    oxi.element: oxi.oxidation_rate for oxi in oxidations
}
print(f"oxidation rates: {oxidation_rates}")