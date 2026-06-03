export type NodesType = 'ACTION' | 'LLM' | 'TRANSFORM' | 'API' | 'DATA_SOURCE' | 'CONTROL_FLOW' | 'TRIGGER';
export type EdgesType = 'linear' | 'if' | 'switch' | 'parallel' | 'merge';

export interface Node {
  key: string;
  name: string;
  type: NodesType;
  inputs: Record<string, any>;
  config: Record<string, any>;
  outputs: Record<string, any>;
  input_model?: Record<string, any>;
  output_model?: Record<string, any> | null;
}

export interface Edge {
  source: string;
  target: string;
  type: EdgesType;
  decision?: boolean | null;
  case?: string | null;
}

export interface Workflow {
  workflow_id?: string;
  name: string;
  description: string;
  nodes: Node[];
  edges: Edge[];
  visibility: 'public' | 'private';
  stars?: number;
  created_by?: string;
}

// Available application node registry specifications
export interface AppNodeSpec {
  key: string;
  name: string;
  type: NodesType;
  description: string;
  service?: string | null;
  valid_permissions?: string[] | null;
  defaultInputs: Record<string, any>;
  defaultConfig: Record<string, any>;
}


// Static definition catalog mapping backend nodes.py keys
export const NODE_SPEC_CATALOG: Record<string, AppNodeSpec> = {
  'llm.groq': {
    key: 'llm.groq',
    name: 'Groq LLM',
    type: 'LLM',
    description: 'Call Groq LLM model with system instructions and JSON response model schemas.',
    service: 'groq',
    defaultInputs: {
      prompt: 'Write advantages of AI.',
    },
    defaultConfig: {
      model: 'llama-3.3-70b-versatile',
      system_prompt: 'You are a helpful AI Assistant.',
      response_model: {
        output: {
          advantages: 'str'
        }
      }
    }
  },
  'llm.google': {
    key: 'llm.google',
    name: 'Gemini LLM',
    type: 'LLM',
    description: 'Call Google Gemini models for structured text processing.',
    service: 'google',
    defaultInputs: {
      prompt: 'Summarize the text.',
    },
    defaultConfig: {
      model: 'gemini-2.5-flash',
      system_prompt: 'You are a helpful AI Assistant.',
      temperature: 0.7,
      max_output_tokens: 1000
    }
  },
  'drive.upload': {
    key: 'drive.upload',
    name: 'Drive Upload',
    type: 'ACTION',
    description: 'Upload a file or textual content onto Google Drive.',
    service: 'google.drive',
    valid_permissions: ['drive.fullaccess', 'drive.file'],
    defaultInputs: {
      content_ref: '',
      filename: 'document.txt',
      mime_type: 'text/plain'
    },
    defaultConfig: {}
  },
  'gmail.send': {
    key: 'gmail.send',
    name: 'Gmail Send Email',
    type: 'ACTION',
    description: 'Send an email with customized to, subject, and body fields.',
    service: 'google.gmail',
    valid_permissions: ['gmail.send', 'gmail.compose'],
    defaultInputs: {
      to: [],
      subject: 'wFlow Automated Alert',
      body: ''
    },
    defaultConfig: {}
  },
  'gmail.create_draft_email': {
    key: 'gmail.create_draft_email',
    name: 'Gmail Create Draft',
    type: 'ACTION',
    description: 'Create an email draft inside Gmail labels.',
    service: 'google.gmail',
    valid_permissions: ['gmail.compose', 'gmail.modify'],
    defaultInputs: {
      to: [],
      subject: 'Draft Alert',
      body: ''
    },
    defaultConfig: {}
  },
  'gmail.get_label_data': {
    key: 'gmail.get_label_data',
    name: 'Gmail Get Label Details',
    type: 'ACTION',
    description: 'Retrieve detailed information for a specific Gmail Label.',
    service: 'google.gmail',
    valid_permissions: ['gmail.readonly', 'gmail.labels'],
    defaultInputs: {
      label_id: 'INBOX'
    },
    defaultConfig: {}
  },
  'gmail.list_gmail_labels': {
    key: 'gmail.list_gmail_labels',
    name: 'Gmail List Labels',
    type: 'ACTION',
    description: 'Lists all available Gmail labels (built-in and custom).',
    service: 'google.gmail',
    valid_permissions: ['gmail.readonly'],
    defaultInputs: {},
    defaultConfig: {}
  },
  'sheets.create_google_sheet': {
    key: 'sheets.create_google_sheet',
    name: 'Sheets Create Sheet',
    type: 'ACTION',
    description: 'Create a brand new Google Sheets document.',
    service: 'google.sheets',
    valid_permissions: ['sheets.fullaccess', 'drive.file'],
    defaultInputs: {
      title: 'wFlow Automation Sheet'
    },
    defaultConfig: {}
  },
  'sheets.read_cell_values': {
    key: 'sheets.read_cell_values',
    name: 'Sheets Read Cells',
    type: 'ACTION',
    description: 'Read range values from a specified Google Sheet.',
    service: 'google.sheets',
    valid_permissions: ['sheets.readonly'],
    defaultInputs: {
      spreadsheet_id: '',
      range: 'Sheet1!A1:B10'
    },
    defaultConfig: {}
  },
  'sheets.append_cell_values': {
    key: 'sheets.append_cell_values',
    name: 'Sheets Append Cells',
    type: 'ACTION',
    description: 'Append rows of values at the end of a Google Sheet.',
    service: 'google.sheets',
    valid_permissions: ['sheets.fullaccess'],
    defaultInputs: {
      spreadsheet_id: '',
      range: 'Sheet1!A1',
      value_input_option: 'RAW',
      values: []
    },
    defaultConfig: {}
  },
  'sheets.update_cell_values': {
    key: 'sheets.update_cell_values',
    name: 'Sheets Update Cells',
    type: 'ACTION',
    description: 'Update cells in a specific cell block range.',
    service: 'google.sheets',
    valid_permissions: ['sheets.fullaccess'],
    defaultInputs: {
      spreadsheet_id: '',
      range: 'Sheet1!A1',
      value_input_option: 'RAW',
      values: []
    },
    defaultConfig: {}
  },
  'if_node': {
    key: 'if_node',
    name: 'If Condition',
    type: 'CONTROL_FLOW',
    description: 'Check a dynamic boolean expression with values and divert flow.',
    defaultInputs: {
      condition: 'word_count >= min_words',
      values: {
        word_count: '',
        min_words: 500
      }
    },
    defaultConfig: {}
  },
  'switch_node': {
    key: 'switch_node',
    name: 'Switch Case',
    type: 'CONTROL_FLOW',
    description: 'Matches a value against several branches and routes flow accordingly.',
    defaultInputs: {
      value: '',
      cases: ['blog', 'newsletter', 'social'],
      default: 'blog'
    },
    defaultConfig: {}
  }
};