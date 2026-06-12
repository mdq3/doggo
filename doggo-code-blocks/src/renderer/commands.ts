export interface PoseCommand {
  blockType: string;
  label: string;
  style: string;
  importLine: string;
  functionName: string;
}

export interface MotionCommand extends PoseCommand {
  param: string; // Python kwarg name, e.g. 'steps'; Blockly input = param.toUpperCase()
  defaultValue: number; // toolbox shadow default
}

export type CommandDef = PoseCommand | MotionCommand;

export const POSE_COMMANDS: PoseCommand[] = [
  {
    blockType: 'doggo_stand',
    label: 'stand',
    style: 'list_blocks',
    importLine: 'from poses import stand',
    functionName: 'stand',
  },
  {
    blockType: 'doggo_sit',
    label: 'sit',
    style: 'list_blocks',
    importLine: 'from poses import sit',
    functionName: 'sit',
  },
  {
    blockType: 'doggo_rest',
    label: 'rest',
    style: 'list_blocks',
    importLine: 'from poses import rest',
    functionName: 'rest',
  },
];

export const TRICK_COMMANDS: PoseCommand[] = [
  {
    blockType: 'doggo_wave',
    label: 'wave',
    style: 'math_blocks',
    importLine: 'from behaviors import wave',
    functionName: 'wave',
  },
  {
    blockType: 'doggo_high_five',
    label: 'high five',
    style: 'math_blocks',
    importLine: 'from behaviors import high_five',
    functionName: 'high_five',
  },
  {
    blockType: 'doggo_handshake',
    label: 'handshake',
    style: 'math_blocks',
    importLine: 'from behaviors import handshake',
    functionName: 'handshake',
  },
  {
    blockType: 'doggo_pee',
    label: 'pee',
    style: 'math_blocks',
    importLine: 'from behaviors import pee',
    functionName: 'pee',
  },
  {
    blockType: 'doggo_play_dead',
    label: 'play dead',
    style: 'math_blocks',
    importLine: 'from behaviors import play_dead',
    functionName: 'play_dead',
  },
  {
    blockType: 'doggo_push_ups',
    label: 'push-ups',
    style: 'math_blocks',
    importLine: 'from behaviors import push_ups',
    functionName: 'push_ups',
  },
  {
    blockType: 'doggo_moonwalk',
    label: 'moonwalk',
    style: 'math_blocks',
    importLine: 'from behaviors import moonwalk',
    functionName: 'moonwalk',
  },
  {
    blockType: 'doggo_boxing',
    label: 'boxing',
    style: 'math_blocks',
    importLine: 'from behaviors import boxing',
    functionName: 'boxing',
  },
];

export const MOTION_COMMANDS: MotionCommand[] = [
  {
    blockType: 'doggo_walk',
    label: 'walk',
    style: 'logic_blocks',
    importLine: 'from gaits.walk import walk',
    functionName: 'walk',
    param: 'steps',
    defaultValue: 2,
  },
  {
    blockType: 'doggo_walk_back',
    label: 'walk back',
    style: 'logic_blocks',
    importLine: 'from gaits.walk_back import walk_back',
    functionName: 'walk_back',
    param: 'steps',
    defaultValue: 2,
  },
  {
    blockType: 'doggo_turn_left',
    label: 'turn left',
    style: 'logic_blocks',
    importLine: 'from gaits.turn import turn_left',
    functionName: 'turn_left',
    param: 'steps',
    defaultValue: 2,
  },
  {
    blockType: 'doggo_turn_right',
    label: 'turn right',
    style: 'logic_blocks',
    importLine: 'from gaits.turn import turn_right',
    functionName: 'turn_right',
    param: 'steps',
    defaultValue: 2,
  },
  {
    blockType: 'doggo_pivot_left',
    label: 'pivot left',
    style: 'logic_blocks',
    importLine: 'from gaits.pivot import pivot_left',
    functionName: 'pivot_left',
    param: 'steps',
    defaultValue: 2,
  },
  {
    blockType: 'doggo_pivot_right',
    label: 'pivot right',
    style: 'logic_blocks',
    importLine: 'from gaits.pivot import pivot_right',
    functionName: 'pivot_right',
    param: 'steps',
    defaultValue: 2,
  },
  {
    blockType: 'doggo_trot',
    label: 'trot',
    style: 'logic_blocks',
    importLine: 'from gaits.trot import trot_forward',
    functionName: 'trot_forward',
    param: 'steps',
    defaultValue: 2,
  },
];
