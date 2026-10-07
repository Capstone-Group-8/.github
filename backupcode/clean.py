import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import main
db = next(main.get_db())

#main.crud.delete_change(db, 1)
#main.crud.delete_change(db, 2)
# main.crud.delete_change(db, 3)
# main.crud.delete_change(db, 4)
# main.crud.delete_change(db, 5)
# main.crud.delete_change(db, 6)
# main.crud.delete_change(db, 7)
# main.crud.delete_change(db, 8)
# main.crud.delete_change(db, 9)
# main.crud.delete_change(db, 10)
#print(main.crud.get_all_changes(db))
print(main.crud.get_invoices(db))