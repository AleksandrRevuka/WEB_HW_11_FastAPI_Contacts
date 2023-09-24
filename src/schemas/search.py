from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.database.models import AddressBookContact, Contact


class ContactFilter(Filter):
    order_by: Optional[List[str]]
    search: Optional[str]
    
    class Constants(Filter.Constants):
        model = Contact
        search_field_name = "search"
        search_model_fields = ["contact_value"]
        

class AddressbookFilter(Filter):
    fullname__ilike: Optional[str]
    contacts: Optional[ContactFilter] = FilterDepends(with_prefix("contact", ContactFilter))
    
    order_by: Optional[List[str]]
    

    class Constants(Filter.Constants):
        model = AddressBookContact
        search_field_name = "fullname"
        search_model_fields = ["first_name", "last_name"]


