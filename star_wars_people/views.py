import petl as etl
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView

from star_wars_people.models import SWPeopleCollection


class HomePage(ListView):
    template_name = 'homepage.html'
    queryset = SWPeopleCollection.objects.all().order_by('-id')

    @staticmethod
    def post(*args, **kwargs) -> HttpResponseRedirect:
        # process data
        SWPeopleCollection.objects.download_new_collection()
        return redirect(reverse('homepage'))


class CollectionDetailsView(DetailView):
    template_name = 'collection_details.html'
    queryset = SWPeopleCollection.objects.all()

    page_size = 10

    def get_context_data(self, **kwargs) -> dict:
        c = super().get_context_data(**kwargs)
        table = self.object.get_table()
        buttons = etl.header(table)
        offset = int(self.request.GET.get('offset', 1))
        offset_to = offset * self.page_size

        if aggregation_keys := tuple(set(buttons).intersection(set(self.request.GET.keys()))):
            table = self.object.get_aggregate_data(aggregation_keys)

        # this is essentially to speed up rendering as it would be slow in django template
        # putting this in templatetag would be more elegant - extend petl to render html directly into a template
        # would also be nice
        data = ''
        for row in etl.data(table, 0, offset_to):
            data += '<tr><td>'+'</td><td>'.join(row)+'</td></tr>'
        c.update({
            'headers': etl.header(table),
            'buttons': buttons,
            'data': data,
            'offset': offset+1,
            'offset_extra_params': '&'.join(['{}=on'.format(i) for i in aggregation_keys]),
            'offset_reached': table.len() < offset_to,
            'aggregation_keys': aggregation_keys
        })
        return c
