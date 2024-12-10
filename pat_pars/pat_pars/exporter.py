from scrapy.exporters import CsvItemExporter

class MyProjectCsvItemExporter(CsvItemExporter):
    def __init__(self, *args, **kwargs):
        kwargs['encoding'] = 'utf-8'
        kwargs['delimiter'] = '╡'
        super(MyProjectCsvItemExporter, self).__init__(*args, **kwargs)