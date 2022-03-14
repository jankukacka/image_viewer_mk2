# ------------------------------------------------------------------------------
#  File: panel_pipelines.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Panel with pipeline details for each channel
#  This widget does not respect the MVP architecture and for simplicity purpose
#  handles communication with the model on its own.
# ------------------------------------------------------------------------------

import tkinter as tk
import tkinter.ttk as ttk

try:
    from . import filter_config
    from . import sortable_accordion
    from ..utils import event_handler
except ImportError:
    from tk_widgets import filter_config
    from tk_widgets import sortable_accordion
    from utils import event_handler

class PanelPipelines(object):
    def __init__(self, parent, skin, var_selected_channel):
        self.parent = parent
        self.skin = skin
        self.var_selected_channel = var_selected_channel
        self.channel_variables = []

        self.accordions = []

    @event_handler.requires('event')
    def on_channels_updated(self, event):
        if event.action == 'itemsAdded':
            for i,item in enumerate(event.items):
                self.add_item(channel_prop=item, channel_index=event.index+i)
        elif event.action == 'itemsRemoved':
            for item in event.items:
                self.remove_item(event.index)

    def add_item(self, channel_prop, channel_index):
        accordion = sortable_accordion.SortableAccordion(self.parent, self.skin)

        for filter in channel_prop['pipeline']['filters']:
            self.create_widget(accordion, filter)

        accordion.pp_observer = event_handler.ObservableEventHandler(self.on_sourceupdatded, accordion=accordion)
        accordion.pp_observer_target = channel_prop['pipeline']['filters']
        channel_prop['pipeline']['filters'].attach(accordion.pp_observer)

        handler = event_handler.ObservableEventHandler(self.update_source, source_list=channel_prop['pipeline']['filters'])
        accordion.items.attach(handler)
        self.accordions.insert(channel_index, accordion)

    def remove_item(self, index):
        self.accordions[index].destroy()
        self.accordions[index].pp_observer_target.detach(self.accordions[index].pp_observer)
        del self.accordions[index]

    # def recreate_items(self, channel_props):
    #     while len(self.accordions) > 0:
    #         self.accordions[-1].destroy()
    #         self.accordions[-1].pp_observer_target.detach(self.accordions[-1].pp_observer)
    #         del self.accordions[-1]
    #
    #     for channel_prop in channel_props:
    #         accordion = sortable_accordion.SortableAccordion(self.parent, self.skin)
    #
    #         for filter in channel_prop['pipeline']['filters']:
    #             self.create_widget(accordion, filter)
    #
    #         accordion.pp_observer = event_handler.ObservableEventHandler(self.on_sourceupdatded, accordion=accordion)
    #         accordion.pp_observer_target = channel_prop['pipeline']['filters']
    #         channel_prop['pipeline']['filters'].attach(accordion.pp_observer)
    #
    #         handler = event_handler.ObservableEventHandler(self.update_source, source_list=channel_prop['pipeline']['filters'])
    #         accordion.items.attach(handler)
    #         self.accordions.append(accordion)

    def create_widget(self, accordion, filter, index=None):
        T_widget = filter_config.get_filter_widget(filter['name'])
        item = sortable_accordion.AccordionItem(accordion, T_widget.title, self.skin, index=index)
        ## Needed for sorting in case there were mutliple filters of the same type
        item.pp_source_filter = filter
        widget = T_widget(item.content, self.skin)
        widget.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        widget.populate(filter['params'])
        ## Trigger removing a filter from model
        handler = event_handler.TkEventHandler(self.filterwidget_onremove, accordion=accordion, filter=filter)
        widget.btn_remove.command = handler

    @staticmethod
    def filterwidget_onremove(accordion, filter):
        accordion.pp_observer_target.pop(accordion.pp_observer_target.index(filter))

    def on_channel_selected_change(self, channel_index):
        for accordion in self.accordions:
            accordion.pack_forget()
        self.accordions[channel_index].pack(side=tk.TOP, expand=True, fill=tk.BOTH)

    @event_handler.requires('event')
    def on_sourceupdatded(self, event, accordion):
        '''
        Handler of events on model.
        '''
        if event.action == 'itemsAdded':
            for i,item in enumerate(event.items):
                self.create_widget(accordion, item, index=event.index+i)
        elif event.action == 'itemsRemoved':
            for item in event.items:
                accordion.remove_at(event.index)
        elif event.action == 'sorted':
            pass
        elif event.action == 'itemsUpdated':
            ## NOTE: changes to source items are handled by the filter config
            ##       widgets directly
            pass

    @event_handler.requires('event')
    def update_source(self, event, source_list):
        '''
        Handler of sorting events on child accordions.
        Propagates sorting back to model.
        '''
        if event.action == 'sorted':
            acc_items = event.source
            acc_filters = [item.pp_source_filter for item in acc_items]
            source_list.sort(key=acc_filters.index)
