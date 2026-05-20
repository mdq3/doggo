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
