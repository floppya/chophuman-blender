import bpy
from collections import defaultdict
import math
import mathutils


# Define limb parts based on vertex groups
def apply_name_template(template, parts):
    return [template % part for part in parts]
    
def prefix_dfm(*parts):
    return apply_name_template('Dfm%s', parts)
    
def make_group_side_names(side, parts):
    return apply_name_template('%s_' + side, parts)
    
arm_parts = prefix_dfm(
    'Biceps',
    'ElbowFan',
    'ElbowFwd',
    'LoArm1',
    'LoArm2',
    'LoArm3',
    'UpArm1',
    'UpArm2',
    'UpArm3',
    'Wrist-1',
    'Wrist-2',
    'Wrist-3',
)
hand_parts= (
    'Index-1',
    'Index-2',
    'Index-3',
    'Middle-1',
    'Middle-2',
    'Middle-3',
    'Palm-1',
    'Palm-2',
    'Palm-3',
    'Palm-4',
    'Palm-5',
    'Pinky-1',
    'Pinky-2',
    'Pinky-3',
    'Ring-1',
    'Ring-2',
    'Ring-3',
    'Thumb-1',
    'Thumb-2',
    'Thumb-3',
)
upper_leg_parts = prefix_dfm(
    'UpLeg1',
    'UpLeg2',
)
lower_leg_parts = prefix_dfm(
    'KneeFan',
    'KneeBack',
    'LoLeg',
)
feet_parts = prefix_dfm(
    'Toe',
    'Foot',
)
head_parts = (
    'DfmHead',
    'DfmLoLid_L',
    'DfmLoLid_R',
    'DfmUpLid_L',
    'DfmUpLid_R',
    'DfmNeck',
    'Eye_L',
    'Eye_R',
    'TongueBase',
    'TongueMid',
    'TongueTip',
    'Jaw',
)
torso_parts = prefix_dfm(
    'Clavicle',
    'Breast_L',
    'Breast_R',
    'Hips',
    'LegOut_L',
    'LegOut_R',
    'Pect2_L',
    'Pect2_R',
    'Scapula',
    'Spine1',
    'Spine2',
    'Spine3',
    'Stomach',
    'Trap2',
)
LIMB_CONFIG = [ # order for painter's algorithm
    ('chop_right_foot', make_group_side_names('R', feet_parts)),
    ('chop_right_lower_leg', make_group_side_names('R', lower_leg_parts)),
    ('chop_right_leg', make_group_side_names('R', upper_leg_parts)),
    
    ('chop_right_hand', make_group_side_names('R', hand_parts)),
    ('chop_right_arm', make_group_side_names('R', arm_parts)),

    ('chop_head', head_parts),
    ('chop_torso', torso_parts),
    
    ('chop_left_foot', make_group_side_names('L', feet_parts)),
    ('chop_left_lower_leg', make_group_side_names('L', lower_leg_parts)),
    ('chop_left_leg', make_group_side_names('L', upper_leg_parts)),
    
    ('chop_left_hand', make_group_side_names('L', hand_parts)),
    ('chop_left_arm', make_group_side_names('L', arm_parts)),        
]
LIMB_CONFIG.reverse() # HACK: the photoshop plugin actually wants them the other way around.


def pose_human(obj):
    """ Position the arms. """
    left_bone = obj.pose.bones['UpArm_L']
    right_bone = obj.pose.bones['UpArm_R']
    left_bone.matrix *= mathutils.Matrix.Rotation(math.radians(-85.0), 4, 'X')
    right_bone.matrix *= mathutils.Matrix.Rotation(math.radians(-85.0), 4, 'X')

   
def create_limb_groups(obj, new_group_name, group_names, threshold=0.3):
    """
    Aggregates the named vertex groups on this object into one large group which
    is associated with a MaskModifier to isolate the limb during rendering.
    """
    original_groups = obj.vertex_groups
    relevant_groups = []
    for group_name in group_names:
        this_group = original_groups.get(group_name)
        if this_group is None:
            continue
        relevant_groups.append(this_group)
    mesh = obj.data       
    meta_group = obj.vertex_groups.new(name=new_group_name)
    indices = set()
    for vert in mesh.vertices:
        for group in relevant_groups:
            try:
                this_weight = group.weight(vert.index)
            except RuntimeError: # vertex not in group
                this_weight = -100.0
            if this_weight >= threshold:
                indices.add(vert.index)
    print('adding group and mask %s' % (meta_group.name))
    meta_group.add(list(indices), 1.0, 'ADD')
    mask_modifier = obj.modifiers.new('LimbMask_' + meta_group.name, 'MASK')
    mask_modifier.vertex_group = meta_group.name
    mask_modifier.show_render = mask_modifier.show_viewport = False

        
def render_limbs(objs, limb_group_names):
    """
    Renders each limb in isolation using the masks we created earlier.
    """
    # arrange scene for rendering
    scene = bpy.context.scene
    render = scene.render
    render.alpha_mode = 'STRAIGHT'
    render.image_settings.color_mode = 'RGBA'
    render.use_full_sample = True
    render.resolution_x, render.resolution_y = (1080, 1920)
    # TODO: Use the object bounds to calculate the ideal camera position?
    camera = bpy.data.cameras['Camera']
    camera.type = 'ORTHO'
    camera.ortho_scale = 28.0 # magic
    camera_obj = bpy.data.objects['Camera']
    camera_obj.rotation_euler = (math.radians(90.0), 0.0, -math.radians(90.0))
    camera_obj.location = (-25.0, 0.0, 12.0)
    light = bpy.data.lamps['Lamp']
    light.type = 'SUN'
    light.shadow_method = 'NOSHADOW' # TODO: Is there a better way to prevent self-shadowing from the hidden vertex groups?
    light_obj = bpy.data.objects['Lamp']
    light_obj.location = (-10.0, 0.0, 10.0)
    light_obj.rotation_euler = (0.0, math.radians(-45.0), 0.0)
    
    # hide all the limbs
    for obj in objs:
        for modifier in obj.modifiers:
            if modifier.name.startswith('LimbMask_'):
                modifier.show_render = modifier.show_viewport = False
    
    # render each limb in isolation
    last_modifiers = []
    for limb_index, limb_group_name in enumerate(limb_group_names):
        # hide the previously displayed limb
        while last_modifiers:
            modifier = last_modifiers.pop()
            modifier.show_render = modifier.show_viewport = False
        for obj in objs:
            mask_name = 'LimbMask_' + limb_group_name
            if not mask_name in obj.modifiers:
                continue
            modifier = obj.modifiers[mask_name]
            modifier.show_render = modifier.show_viewport = True
            last_modifiers.append(modifier)
        # render limb
        filename = 'c:/tmp/%03d_%s.png' % (limb_index, limb_group_name) # TODO: un-hardcode render filepath
        scene.render.filepath = filename
        bpy.ops.render.render(write_still=True)

    
def chop(target_objects, group_threshold=0.5):
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in target_objects:
        pose_human(obj)
    # create a vertex group for each (sub object, limb)
    for limb_group_name, limb_group in LIMB_CONFIG:
        for root_object in target_objects:
            for subobj in root_object.children:
                if subobj.type.lower() == 'mesh':
                    create_limb_groups(subobj, limb_group_name, limb_group, threshold=group_threshold)
    
    
def render(target_objects):
    relevant_objs = []
    for limb_group_name, limb_group in LIMB_CONFIG:
        for root_object in target_objects:
            for subobj in root_object.children:
                if subobj.type.lower() == 'mesh':                        
                    relevant_objs.append(subobj) 
    render_limbs(relevant_objs, [name for name, groups in LIMB_CONFIG])

    
class ChopHumanOperator(bpy.types.Operator):
    """ The Choperator. """
    bl_idname = 'chophuman.chop_it'
    bl_label = 'Chop'

    def execute(self, context):    
        # TODO: UI for threshold?
        chop(context.selected_objects, group_threshold=0.0)
        return {'FINISHED'}

        
class RenderChoppedHumanOperator(bpy.types.Operator):
    """ Render the chopped limbs. """
    bl_idname = 'chophuman.render_limbs'
    bl_label = 'Render'

    def execute(self, context):    
        render(context.selected_objects)
        return {'FINISHED'}

        
class ChopHumanPanel(bpy.types.Panel):
    bl_idname = 'ChopHumanPanel'
    bl_label = 'Chop Human'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('chophuman.chop_it')
        row = layout.row()
        row.operator('chophuman.render_limbs')

