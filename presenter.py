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
    from .windnd import hook_dropfiles
except ImportError:
    import view as view_
    from windnd import hook_dropfiles

class Presenter(object):
    '''
    '''

    def __init__(self, view, model):
        self.view = view
        self.model = model
        # filename = self.view.asksaveasfilename(title='Save render as...', filetypes=[('Numpy files', '.npy')], initialfile='render.npy')

        ## Init view from model
        # self.color_onchage()
        # self.view.var_colorspace.set(self.model.color_space)
        # for var, color in zip(self.view.var_color, self.model.colors):
        #     var.set(color)
        # for obj, var in zip(self.view.color_previews, self.view.var_color):
        #     obj.config(background=var.get())
        # cmap2d.plot_cmap(self.model.colormap, self.view.axis_cmap)
        # self.view.figure_canvas.draw()

        ## Define view callbacks
        ## -- Update color previews
        # for obj, var in zip(self.view.color_previews, self.view.var_color):
        #     var.trace('w', lambda _1,_2,_3, obj=obj, var=var: self.update_widget_bkg(obj,var))
        self.view.var_channel['color'].trace('w', lambda _1,_2,_3, obj=self.view.color_preview, var=self.view.var_channel['color']: self.update_widget_bkg(obj,var))

        # ## -- color space changes
        # self.view.var_colorspace.trace('w', lambda _1,_2,_3, var=view.var_colorspace: self.colorspace_onchange(var))

        ## -- Color picker clicks
        # for btn, var in zip(view.color_pickers, self.view.var_color):
        self.view.color_picker.config(command=lambda var=self.view.var_channel['color']: self.pick_color(var))

        ## -- Update colormap preview
        # for index, var in enumerate(self.view.var_color):
        self.view.var_channel['color'].trace('w', lambda _1,_2,_3: self.color_onchage())

        ## -- channel property changes
        self.view.var_selected_channel.trace('w', lambda _1,_2,_3, self=self: self.channel_onchange())
        for key,var in self.view.var_channel.items():
            var.trace('w', lambda _1,_2,_3,var=var,key=key: self.channel_var_onchange(var,key))

        # ## -- image option changes
        # for key,var in self.view.var_imoptions.items():
        #     var.trace('w', lambda _1,_2,_3,var=var,key=key: self.imoption_var_onchange(var,key))

        ## -- channel control buttons
        self.view.channels_panel.btn_hide_all.config(command=self.hide_all)
        self.view.channels_panel.btn_show_all.config(command=self.show_all)

        ## -- config saving and loading
        self.view.btn_save.config(command=self.save_model)
        self.view.btn_load.config(command=self.load_model)
        self.view.btn_save_render.config(command=self.save_render)

        ## -- config copying and pasting
        self.view.btn_paste.config(command=lambda: self.model.paste_params(self.view.get_active_channel()))
        self.view.btn_copy.config(command=lambda: self.model.copy_params(self.view.get_active_channel()))

        ## -- clipboard
        self.view.bind('<Control-c>', self.render_to_clipboard)
        self.view.bind('<Control-s>', self.save_render)
        self.view.bind('<Control-o>', self.load_image)
        self.view.bind('<Control-t>', lambda _: self.model.transpose_image())

        ## -- bind menu commands
        self.view.menu['file']['obj'].entryconfig(self.view.menu['file']['load_image'], command=self.load_image)
        self.view.menu['file']['obj'].entryconfig(self.view.menu['file']['save_render'], command=self.save_render)
        self.view.menu['file']['obj'].entryconfig(self.view.menu['file']['save_config'], command=self.save_model)
        self.view.menu['file']['obj'].entryconfig(self.view.menu['file']['load_config'], command=self.load_model)
        self.view.menu['image']['obj'].entryconfig(self.view.menu['image']['transpose'], command=self.model.transpose_image)
        self.view.menu['image']['obj'].entryconfig(self.view.menu['image']['autocolor'], command=self.model.autocolor)


        ## -- on closing
        # self.protocol("WM_DELETE_WINDOW", self.on_closing)

        ## Define model callbacks
        self.model.attach(self.model_onchange)

        ## Hook on model rendering updates
        self.check_model_for_render()

        ## Hook drag'n'drop files
        hook_dropfiles(self.view, self.drag_file)

    def register_channel_panel_handlers(self):
        ## Register handlers on variables of channels panel
        for i,var_channel in enumerate(self.view.channels_panel.var_channels):
            for key,var in var_channel.items():
                # if key != 'name':  ## Name has a seperate handling mechanism
                var.trace('w', lambda _1,_2,_3,var=var,key=key,cindex=i: self.channel_var_onchange(var,key,cindex))

        for i, color_preview in enumerate(self.view.channels_panel.color_previews):
            color_preview.bind('<Double-Button-1>', lambda _, var=self.view.channels_panel.var_channels[i]['color']: self.pick_color(var))


    def check_model_for_render(self):
        self.model.check_for_render()
        self.view.after(50, self.check_model_for_render)

    def check_model_for_io(self):
        self.model.check_for_io()
        if self.model.n_io_pending > 0:
            self.view.after(50, self.check_model_for_io)
        else:
            self.view.loader.hide()


    def model_onchange(self, event):
        '''
        Propagates changes in the model to the view.
        '''
        if event.action == 'ioTask':
            self.view.loader.show()
            self.check_model_for_io()
        if event.action == 'propertyChanged':
            # if event.propertyName == 'colors':
            #     channel_index = self.view.get_active_channel()
            #     self.view.var_channel['color'].set(self.model.colors[channel_index])
                # for var, color in zip(self.view.var_color, self.model.colors):
                #     var.set(color)
            # if event.propertyName == 'colormap':
            #     self.update_colormap()
            # if event.propertyName == 'color_space':
            #     self.view.var_colorspace.set(self.model.color_space)
            # if event.propertyName == 'channel_properties':
            #     for i, channel_property in enumerate(self.model.channel_properties):
            #         for key, val in channel_property.items():
            #             self.view.var_channel[i][key].set(val)
            #             if key in self.view.property_frames[i]:
            #                 view_.set_state(self.view.property_frames[i][key], 'normal' if val else 'disable')

            if event.propertyName == 'channel_props':
                # print(event)
                if hasattr(event, 'child'):
                    if event.child.action == 'itemsAdded' or event.child.action == 'itemsRemoved':
                        self.view.update_channels(self.model.channel_props)
                        self.register_channel_panel_handlers()

                self.view.channels_panel.update_vars(self.model.channel_props)
                active_channel = self.view.get_active_channel()
                if active_channel < len(self.model.channel_props):
                    self.channel_onchange()
                    # channel_property = self.model.channel_props[active_channel]
                    # for key, val in channel_property.items():
                    #     if key in self.view.var_channel:
                    #         self.view.var_channel[key].set(val)
                    #     if key in self.view.property_frames:
                    #         view_.set_state(self.view.property_frames[key], 'normal' if val else 'disable')

            if event.propertyName == 'imoptions':
                for key, val in self.model.imoptions.items():
                    self.view.var_imoptions[key].set(val)
                    if key in self.view.imoption_frames:
                        view_.set_state(self.view.imoption_frames[key], 'normal' if val else 'disable')

            if event.propertyName == 'render':
                if self.model.render is not None:
                    self.view.show_image(self.model.render)

                if self.model.response_images is not None:
                    channel_index = self.view.get_active_channel()
                    self.view.show_response(self.model.response_images[channel_index])


    def save_model(self):
        model_dict = self.model.save()
        filename = self.view.asksaveasfilename(title='Save config as...', filetypes=[('JSON files', '.json')], initialfile='config.json')
        try:
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

    def color_onchage(self):
        channel_index = self.view.get_active_channel()
        var = self.view.var_channel['color']
        color = var.get()
        if is_color_like(color) and channel_index < len(self.model.channel_props):
            self.model.channel_props[channel_index]['color'] = str(to_hex(color))

    # def colorspace_onchange(self, var):
    #     self.model.color_space = var.get()

    def channel_var_onchange(self, var, key, cindex=None):
        if cindex is None:
            cindex = self.view.get_active_channel()
        self.model.channel_props[cindex][key] = var.get()

    def imoption_var_onchange(self, var, key):
        self.model.imoptions[key] = var.get()

    def update_colormap(self):
        pass
        # x = self.model.responses[0][1]
        # y = self.model.responses[1][1]
        # xx,yy = np.meshgrid(x,y)
        # coords = np.stack([xx,yy], axis=-1)
        # preview = self.model.colormap(coords)
        # self.view.axis_cmap.imshow(preview)
        # # cmap2d.plot_cmap(self.model.colormap, self.view.axis_cmap)
        # self.view.figure_cmap_canvas.draw()

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

    def hide_all(self, *_):
        cindex = self.view.get_active_channel()
        for i in range(len(self.model.channel_props)):
            if i != cindex:
                self.model.channel_props[i]['visible'] = False

    def show_all(self, *_):
        for i in range(len(self.model.channel_props)):
            self.model.channel_props[i]['visible'] = True

    def render_to_clipboard(self, _):
        '''
        Code from https://stackoverflow.com/a/62007792/2042751
        '''
        from io import BytesIO
        import win32clipboard
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
