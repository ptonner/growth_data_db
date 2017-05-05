from wtforms.validators import ValidationError
import pandas as pd

class SourceValidator(object):
    """Validator base class for data files in plate creation form."""

    def __init__(self, message=None):
        self.message = message

    def validate(self, form, field):
        raise NotImplemented()

    def __call__(self, form, field):
        if field.data is None:
            message = self.message or 'A data file is required'
            raise ValidationError(self.message)

        self.validate(form, field)

class CsvValidator(SourceValidator):

    def validate(self,form, field):
        self.data = pd.read_csv(field.data)

class BioscreenValidator(CsvValidator):

    def __init__(self, message=None):

        if message is None:
            message = 'Bioscreen validation failed!'

        CsvValidator.__init__(self, message)

    def validate(self, form, field):
        CsvValidator.validate(self, form, field)

        if not self.data.shape[1] == 202:
            raise ValidationError(self.message)

        if not self.data.columns[0] == 'Time':
            raise ValidationError(self.message)

        if not self.data.columns[1] == 'Blank':
            raise ValidationError(self.message)

        for i in range(200):
            if not self.data.columns[2+i] == '%d'%i+101:
                raise ValidationError(self.message)

class DataValidator():

    def __init__(self, message=None):
        if message is None:
            message = 'Data validation failed!'

    def __call__(self, form, field):
        if form.source == 'bioscreen':
            BioscreenValidator()(form, field)
