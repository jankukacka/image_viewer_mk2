# ------------------------------------------------------------------------------
#  File: panel_pipelines.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Panel with pipeline details for each channel
# ------------------------------------------------------------------------------

import tkinter as tk
import tkinter.ttk as ttk

try:
    from . import filter_config
    from . import sortable_accordion
except ImportError:
    from tk_widgets import filter_config
    from tk_widgets import sortable_accordion

class PanelPipelines(object):
    def __init__(self, parent, skin, var_selected_channel):
        self.parent = parent
        self.skin = skin
        self.var_selected_channel = var_selected_channel
        self.channel_variables = []

        self.accordions = []

    def recreate_items(self, channel_props):
        while len(self.accordions) > 0:
            self.accordions[-1].destroy()
            del self.accordions[-1]

        for channel_prop in channel_props:
            accordion = sortable_accordion.SortableAccordion(self.parent, self.skin)

            for filter in channel_prop['pipeline']['filters']:
                self.create_widget(accordion, filter)

            channel_prop['pipeline']['filters'].attach(lambda e, self=self, accordion=accordion: self.on_sourceupdatded(e, accordion))
            self.accordions.append(accordion)

    def create_widget(self, accordion, filter, index=None):
        T_widget = filter_config.get_filter_widget(filter['name'])
        item = sortable_accordion.AccordionItem(accordion, T_widget.title, self.skin, index=index)
        widget = T_widget(item.content, self.skin)
        widget.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        widget.populate(filter['params'])

    def on_channel_selected_change(self, channel_index):
        for accordion in self.accordions:
            accordion.pack_forget()
        self.accordions[channel_index].pack(side=tk.TOP, expand=True, fill=tk.BOTH)

    def on_sourceupdatded(self, event, accordion):
        if event.action == 'itemsAdded':
            for i,item in enumerate(event.items):
                self.create_widget(accordion, item, index=event.index+i)
        elif event.action == 'itemsRemoved':
            for item in event.items:
                accordion.remove_at(event.index)
        elif event.action == 'sorted':
            pass
