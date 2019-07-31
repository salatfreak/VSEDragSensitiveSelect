# Add-on meta data
bl_info = {
    "name": "Drag Sensitive Select Operator",
    "description": "Move multiple selected strips by clicking and dragging",
    "author": "Salatfreak",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "Video Sequence Editor",
    "wiki_url": "https://github.com/Salatfreak/VSEDragSensitiveSelect",
    "tracker_url": "https://github.com/Salatfreak/VSEDragSensitiveSelect/issues",
    "category": "Sequencer",
}

# Import modules
import bpy

# Select operator
class DragSensitiveSelectOperator(bpy.types.Operator):
    bl_idname = "sequencer.drag_sensitive_select"
    bl_label = "Drag Sensitive Select"
    
    # Only show if select enabled
    @classmethod
    def poll(cls, context):
        return bpy.ops.sequencer.select.poll()
    
    # Start modal execution
    def invoke(self, context, event):
        # Get mouse button roles
        keyconfig = context.window_manager.keyconfigs.active
        self._select = getattr(keyconfig.preferences, 'select_mouse', 'LEFT') + 'MOUSE'
        self._cancel = 'RIGHTMOUSE' if self._select == 'LEFTMOUSE' else 'LEFTMOUSE'
        
        # Only do something if invoked by select mouse button
        if event.type != self._select: return {'CANCELLED'}
        
        # Get mouse position, frame and channel
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        view = context.area.regions[3].view2d
        frame, channel = view.region_to_view(mouse_x, mouse_y)
        
        strip = next((
            s for s in context.scene.sequence_editor.sequences
            if s.channel == int(channel) \
                and s.frame_final_start <= frame and frame < s.frame_final_end
        ), None)      
        
        # Do nothing if not a selected strip or only one selected
        if strip is None or not strip.select: return {'PASS_THROUGH'}
        if len(context.selected_sequences) == 1: return {'PASS_THROUGH'} 
        
        # Get handle selections
        select_left = strip.select_left_handle
        select_right = strip.select_right_handle
        
        # Deselect strip
        strip.select = False
        strip.select_left_handle = strip.select_right_handle = False
        
        # Expand selection
        bpy.ops.sequencer.select('INVOKE_DEFAULT', extend=True)
        
        # Check if clicked on selected handle or none if none selected
        clicked_on_selected = (
            strip.select_left_handle and select_left or
            strip.select_right_handle and select_right or
            not (
                strip.select_left_handle or strip.select_right_handle or
                select_left or select_right
            )
        )
        
        # Reset selection
        strip.select_left_handle = select_left
        strip.select_right_handle = select_right
        
        # Do nothing if not clicked on selected handle
        if not clicked_on_selected: return {'PASS_THROUGH'}
                
        # Start running modal
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        
    # Handle modal events
    def modal(self, context, event):
        # Invoke sequence slide on mouse move
        if event.type == 'MOUSEMOVE':
            return {'FINISHED', 'PASS_THROUGH'}
        
        # Invoke select on mouse release
        if event.type == self._select:
            return bpy.ops.sequencer.select('INVOKE_DEFAULT')
        
        # Ignore on timer
        if event.type.startswith('TIMER'):
            return {'PASS_THROUGH'}
        
        # Cancel in any other event
        return {'CANCELLED', 'PASS_THROUGH'}

# Register add-on
keymap = None
def register():
    global keymap
    
    # Register operator
    bpy.utils.register_class(DragSensitiveSelectOperator)
    
    # Get mouse button roles
    keyconfig = bpy.context.window_manager.keyconfigs.active
    select_mouse = getattr(keyconfig.preferences, 'select_mouse', 'LEFT') + 'MOUSE'
    
    # Create keymap
    keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
        name='Sequencer', space_type='SEQUENCE_EDITOR'
    )
    keymap.keymap_items.new(DragSensitiveSelectOperator.bl_idname, select_mouse, 'PRESS')

# Unregister add-on
def unregister():
    # Unegister operator
    bpy.utils.unregister_class(DragSensitiveSelectOperator)
    
    # Remove keymap
    for item in keymap.keymap_items: keymap.keymap_items.remove(item)
    
# Register on script execution
if __name__ == '__main__':
    register()