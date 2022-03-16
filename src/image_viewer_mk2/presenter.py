# ------------------------------------------------------------------------------
#  File: presenter.py
#  Author: Jan Kukacka
#  Date: 3/2021
# ------------------------------------------------------------------------------
#  Presenter component
# ------------------------------------------------------------------------------

import numpy as np
import happy as hp
from matplotlib.colors import is_color_like, to_hex

try:
    from . import view as view_
    from .utils.windnd import hook_dropfiles
    from .utils import event_handler
except ImportError:
    import view as view_
    from utils import event_handler
    from utils.windnd import hook_dropfiles

class Presenter(object):
    '''
    '''

    def __init__(self, view, model):
        self.view = view
        self.model = model

        ## Define view callbacks
        ## -- Update color previews
        handler = event_handler.TkVarEventHandler(self.update_widget_bkg, obj=self.view.color_preview, var=self.view.var_channel['color'])
        self.view.var_channel['color'].trace('w', handler)

        ## -- Color picker clicks
        handler = event_handler.TkCommandEventHandler(self.pick_color, var=self.view.var_channel['color'])
        self.view.color_picker.config(command=handler)

        ## -- Channels list - color picker
        self.view.channels_panel.attach(event_handler.ObservableEventHandler(self.pick_color_event,
                                                                             filter_={'action': 'color_preview_onclick'}))

        ## -- Update color preview
        self.view.var_channel['color'].trace('w', event_handler.TkVarEventHandler(self.color_onchage))

        ## -- channel property changes
        self.view.var_selected_channel.trace('w', event_handler.TkVarEventHandler(self.channel_onchange))
        for key,var in self.view.var_channel.items():
            var.trace('w', event_handler.TkVarEventHandler(self.channel_var_onchange, key=key, var=var))

        ## -- channel control buttons
        self.view.channels_panel.btn_hide_all.config(command=event_handler.TkCommandEventHandler(self.hide_all))
        self.view.channels_panel.btn_show_all.config(command=event_handler.TkCommandEventHandler(self.show_all))

        ## -- config saving and loading
        self.view.btn_save.config(command=event_handler.TkCommandEventHandler(self.save_model))
        self.view.btn_load.config(command=event_handler.TkCommandEventHandler(self.load_model))
        self.view.btn_save_render.config(command=event_handler.TkCommandEventHandler(self.save_render))

        ## -- config copying and pasting
        def paste_params(obj):
            obj.model.paste_params(obj.view.get_active_channel())
        self.view.btn_paste.config(command=event_handler.TkCommandEventHandler(paste_params, obj=self))
        def copy_params(obj):
            obj.model.copy_params(obj.view.get_active_channel())
        self.view.btn_copy.config(command=event_handler.TkCommandEventHandler(copy_params, obj=self))

        ## -- clipboard
        self.view.bind('<Control-c>', event_handler.TkEventHandler(self.render_to_clipboard))
        self.view.bind('<Control-s>', event_handler.TkEventHandler(self.save_render))
        self.view.bind('<Control-o>', event_handler.TkEventHandler(self.load_image))
        self.view.bind('<Control-t>', event_handler.TkEventHandler(self.model.transpose_image))

        ## -- bind menu commands
        self.view.menu['file']['obj'].entryconfig(self.view.menu['file']['load_image'], command=event_handler.TkCommandEventHandler(self.load_image))
        self.view.menu['file']['obj'].entryconfig(self.view.menu['file']['save_render'], command=event_handler.TkCommandEventHandler(self.save_render))
        self.view.menu['file']['obj'].entryconfig(self.view.menu['file']['save_config'], command=event_handler.TkCommandEventHandler(self.save_model))
        self.view.menu['file']['obj'].entryconfig(self.view.menu['file']['load_config'], command=event_handler.TkCommandEventHandler(self.load_model))
        self.view.menu['image']['obj'].entryconfig(self.view.menu['image']['transpose'], command=event_handler.TkCommandEventHandler(self.model.transpose_image))
        self.view.menu['image']['obj'].entryconfig(self.view.menu['image']['autocolor'], command=event_handler.TkCommandEventHandler(self.model.autocolor))

        ## -- adding filters
        for key, val in self.view.menu_add_filter.items():
            if key == 'obj': continue
            def add_filter(filter):
                self.model.add_filter(self.view.get_active_channel(), filter_name=filter)
            self.view.menu_add_filter['obj'].entryconfig(
                self.view.menu_add_filter[key],
                command=event_handler.TkCommandEventHandler(add_filter, filter=key))

        ## -- on closing
        # self.protocol("WM_DELETE_WINDOW", self.on_closing)

        ## Attach model callbacks
        self.model.channel_props.attach(event_handler.ObservableEventHandler(
            self.view.channels_panel.on_channels_updated,
            filter_={'action':['itemsAdded', 'itemsRemoved']}))
        self.model.channel_props.attach(event_handler.ObservableEventHandler(
            self.view.pipelines_panel.on_channels_updated,
            filter_={'action':['itemsAdded', 'itemsRemoved']}))
        self.model.channel_props.attach(event_handler.ObservableEventHandler(
            self.view.update_channels, channel_props=self.model.channel_props,
            filter_={'action':['itemsAdded', 'itemsRemoved']}))

        self.model.attach(event_handler.ObservableEventHandler(
            self.model_onioTask, filter_={'action':'ioTask'}))

        self.model.attach(event_handler.ObservableEventHandler(
            self.model_onrender, filter_={'propertyName':'render'}))

        self.model.attach(event_handler.ObservableEventHandler(
            self.model_onchannelpropschange, filter_={'propertyName':'channel_props'}))

        ## Hook on model rendering updates
        self.check_model_for_render()

        ## Hook drag'n'drop files
        hook_dropfiles(self.view, self.drag_file)


    def check_model_for_render(self):
        self.model.check_for_render()
        self.view.after(50, self.check_model_for_render)

    def check_model_for_io(self):
        self.model.check_for_io()
        if self.model.n_io_pending > 0:
            self.view.after(50, self.check_model_for_io)
        else:
            self.view.loader.hide()

    def model_onioTask(self):
        self.view.loader.show()
        self.check_model_for_io()

    def model_onrender(self):
        if self.model.render is not None:
            self.view.show_image(self.model.render)

        if self.model.response_images is not None:
            channel_index = self.view.get_active_channel()
            self.view.show_response(self.model.response_images[channel_index])

    def model_onchannelpropschange(self):
        ## TODO: This could probably be simplified and made more efficient
        self.view.channels_panel.update_vars(self.model.channel_props)
        ## TODO: This could be bound to itemsRemoved only
        active_channel = self.view.get_active_channel()
        if active_channel < len(self.model.channel_props):
            self.channel_onchange()


    def save_model(self):
        model_dict = self.model.save()
        filename = self.view.asksaveasfilename(title='Save config as...', filetypes=[('JSON files', '.json')], initialfile='config.json')
        try:
            if not filename.lower().endswith('.json'):
                filename += '.json'
            hp.io.save(filename, model_dict, overwrite=True)
        except Exception as e:
            print('Error saving model as', filename)
            print(e)

    def load_model(self):
        filename = self.view.askopenfilename(title='Load config file...', filetypes=[('JSON files', '.json')])
        try:
            self.model.load(hp.io.load(filename))
        except Exception as e:
            print(e)

    def load_image(self, *args):
        filename = self.view.askopenfilename(title='Load image...', filetypes=[('NIFTI images', '.nii.gz'), ('Numpy arrays', '.npy'), ('MATLAB', '.mat'), ('NRRD images', '.nrrd')])
        try:
            self.model.filename = filename
        except Exception as e:
            print(e)

    def drag_file(self, files):
        if len(files) > 0:
            ## Model filename update has to be registered using "after",
            ## otherwise the program crashes with:
            ## Fatal Python error: PyEval_RestoreThread: NULL tstate
            filename = files[0].decode()

            ## If file is json, try loading it as a model
            if filename.lower().endswith('.json'):
                def update_model():
                    try:
                        self.model.load(hp.io.load(filename))
                    except Exception as e:
                        print(e)
                self.view.after(10, update_model)
            ## Else try loading it as an image
            else:
                def update_filename():
                    self.model.filename = filename
                self.view.after(10, update_filename)

    def save_render(self, *args):
        filename = self.view.asksaveasfilename(title='Save render as...', filetypes=[('Numpy files', '.npy'), ('PNG', '.png')], initialfile='render.npy')
        try:
            hp.io.save(filename, self.model.render, overwrite=True)
        except Exception as e:
            print('Error saving render as', filename)
            print(e)

    def channel_onchange(self):
        channel_index = self.view.get_active_channel()
        if channel_index < 0 or channel_index >= len(self.model.channel_props):
            return

        channel_property = self.model.channel_props[channel_index]

        for key, val in channel_property.items():
            if key in self.view.var_channel:
                self.view.var_channel[key].set(val)
            if key in self.view.property_frames:
                view_.set_state(self.view.property_frames[key], 'normal' if val else 'disable')

        self.view.channels_panel.highlight_item(channel_index)
        self.view.pipelines_panel.on_channel_selected_change(channel_index)
        if self.model.response_images is not None:
            self.view.show_response(self.model.response_images[channel_index])


    def color_onchage(self):
        channel_index = self.view.get_active_channel()
        var = self.view.var_channel['color']
        color = var.get()
        if is_color_like(color) and channel_index < len(self.model.channel_props):
            self.model.channel_props[channel_index]['color'] = str(to_hex(color))

    def channel_var_onchange(self, var, key, cindex=None):
        if cindex is None:
            cindex = self.view.get_active_channel()
        self.model.channel_props[cindex][key] = var.get()


    @staticmethod
    def update_widget_bkg(obj,var):
        color = var.get()
        try:
            obj.config(background=str(to_hex(color)))
        except:
            pass

    def pick_color(self, var):
        cindex = self.view.get_active_channel()
        color = var.get()
        try:
            response = self.view.askcolor(initialcolor=str(to_hex(color)))
            if response is not None:
                var.set(response)
        except:
            pass

    @event_handler.requires('event')
    def pick_color_event(self, event):
        self.pick_color(event.var)

    def hide_all(self, *_):
        cindex = self.view.get_active_channel()
        self.model.channel_props[cindex]['visible'] = True
        for i in range(len(self.model.channel_props)):
            if i != cindex:
                self.model.channel_props[i]['visible'] = False

    def show_all(self, *_):
        for i in range(len(self.model.channel_props)):
            self.model.channel_props[i]['visible'] = True

    def render_to_clipboard(self):
        '''
        Code from https://stackoverflow.com/a/62007792/2042751
        '''
        try:
            import win32clipboard
        except ImportError:
            print('Cannot import win32clipboard. Copy to clipboard not available.')
            return

        from io import BytesIO
        from PIL import Image

        def send_to_clipboard(clip_type, data):
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(clip_type, data)
            win32clipboard.CloseClipboard()

        # image = self.model.render
        with BytesIO() as stream:
            self.model.render.convert("RGB").save(stream, "BMP")
            data = stream.getvalue()[14:]
            send_to_clipboard(win32clipboard.CF_DIB, data)

    def mainloop(self):
        self.view.mainloop()
