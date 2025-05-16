from django.contrib import admin
from .models import FormulaQuestion
from .models import (
    Formulas,
    Theory,
    Note,
    FavoriteFormula,
    FormulaQuestion,
    TestAttempt
)



admin.site.register(FormulaQuestion)
admin.site.register(Formulas)
admin.site.register(Theory)
admin.site.register(Note)
admin.site.register(FavoriteFormula)
admin.site.register(TestAttempt)

# Register your models here.
