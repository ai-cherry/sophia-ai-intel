/**
 * Tool Schemas - Strict I/O validation for all tool calls
 * ======================================================
 * 
 * Centralized schema definitions for validating inputs and outputs
 * of all tool calls with comprehensive error handling and type safety.
 */

/** Base schema interface */
export interface Schema {
  type: string
  required?: boolean
  description?: string
  validate?: (value: any) => ValidationResult
}

/** String schema with constraints */
export interface StringSchema extends Schema {
  type: 'string'
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  enum?: string[]
}

/** Number schema with constraints */
export interface NumberSchema extends Schema {
  type: 'number'
  minimum?: number
  maximum?: number
  multipleOf?: number
}

/** Boolean schema */
export interface BooleanSchema extends Schema {
  type: 'boolean'
}

/** Array schema */
export interface ArraySchema extends Schema {
  type: 'array'
  items: Schema
  minItems?: number
  maxItems?: number
}

/** Object schema */
export interface ObjectSchema extends Schema {
  type: 'object'
  properties: Record<string, Schema>
  additionalProperties?: boolean
  requiredProps?: string[]
}

/** Union schema for multiple types */
export interface UnionSchema extends Schema {
  type: 'union'
  schemas: Schema[]
}

/** Validation result */
export interface ValidationResult {
  isValid: boolean
  errors: ValidationError[]
  sanitizedValue?: any
}

/** Validation error details */
export interface ValidationError {
  path: string
  message: string
  code: string
  expectedType?: string
  actualType?: string
  value?: any
}

/** Tool definition with input/output schemas */
export interface ToolDefinition {
  name: string
  description: string
  inputSchema: Schema
  outputSchema: Schema
  examples?: Array<{
    input: any
    output: any
    description: string
  }>
}

// Helper functions for creating schemas
export function str(options: Partial<StringSchema> = {}): StringSchema {
  return { type: 'string', ...options }
}

export function num(options: Partial<NumberSchema> = {}): NumberSchema {
  return { type: 'number', ...options }
}

export function bool(options: Partial<BooleanSchema> = {}): BooleanSchema {
  return { type: 'boolean', ...options }
}

export function arr(items: Schema, options: Partial<ArraySchema> = {}): ArraySchema {
  return { type: 'array', items, ...options }
}

export function obj(properties: Record<string, Schema>, options: Partial<ObjectSchema> = {}): ObjectSchema {
  return { type: 'object', properties, ...options }
}

export function union(schemas: Schema[], options: Partial<UnionSchema> = {}): UnionSchema {
  return { type: 'union', schemas, ...options }
}

/** Schema validator class */
export class SchemaValidator {
  /**
   * Validate a value against a schema
   */
  validate(value: any, schema: Schema, path = ''): ValidationResult {
    const errors: ValidationError[] = []
    let sanitizedValue = value

    // Check required
    if (schema.required && (value === undefined || value === null)) {
      errors.push({
        path,
        message: `Field is required`,
        code: 'REQUIRED',
        expectedType: schema.type,
        actualType: typeof value,
        value
      })
      return { isValid: false, errors }
    }

    // Skip validation if value is undefined/null and not required
    if (value === undefined || value === null) {
      return { isValid: true, errors: [], sanitizedValue: value }
    }

    // Type-specific validation
    switch (schema.type) {
      case 'string':
        return this.validateString(value, schema as StringSchema, path)
      case 'number':
        return this.validateNumber(value, schema as NumberSchema, path)
      case 'boolean':
        return this.validateBoolean(value, schema as BooleanSchema, path)
      case 'array':
        return this.validateArray(value, schema as ArraySchema, path)
      case 'object':
        return this.validateObject(value, schema as ObjectSchema, path)
      case 'union':
        return this.validateUnion(value, schema as UnionSchema, path)
      default:
        errors.push({
          path,
          message: `Unknown schema type: ${schema.type}`,
          code: 'UNKNOWN_TYPE',
          value
        })
    }

    return { isValid: errors.length === 0, errors, sanitizedValue }
  }

  private validateString(value: any, schema: StringSchema, path: string): ValidationResult {
    const errors: ValidationError[] = []
    let sanitizedValue = value

    // Type check
    if (typeof value !== 'string') {
      // Try to convert
      if (typeof value === 'number' || typeof value === 'boolean') {
        sanitizedValue = String(value)
      } else {
        errors.push({
          path,
          message: `Expected string, got ${typeof value}`,
          code: 'INVALID_TYPE',
          expectedType: 'string',
          actualType: typeof value,
          value
        })
        return { isValid: false, errors }
      }
    }

    const strValue = sanitizedValue as string

    // Length validation
    if (schema.minLength !== undefined && strValue.length < schema.minLength) {
      errors.push({
        path,
        message: `String too short (min: ${schema.minLength}, actual: ${strValue.length})`,
        code: 'MIN_LENGTH',
        value
      })
    }

    if (schema.maxLength !== undefined && strValue.length > schema.maxLength) {
      errors.push({
        path,
        message: `String too long (max: ${schema.maxLength}, actual: ${strValue.length})`,
        code: 'MAX_LENGTH',
        value
      })
    }

    // Pattern validation
    if (schema.pattern && !schema.pattern.test(strValue)) {
      errors.push({
        path,
        message: `String does not match pattern: ${schema.pattern.source}`,
        code: 'PATTERN_MISMATCH',
        value
      })
    }

    // Enum validation
    if (schema.enum && !schema.enum.includes(strValue)) {
      errors.push({
        path,
        message: `Value not in allowed enum: [${schema.enum.join(', ')}]`,
        code: 'ENUM_MISMATCH',
        value
      })
    }

    return { isValid: errors.length === 0, errors, sanitizedValue }
  }

  private validateNumber(value: any, schema: NumberSchema, path: string): ValidationResult {
    const errors: ValidationError[] = []
    let sanitizedValue = value

    // Type check and conversion
    if (typeof value !== 'number') {
      if (typeof value === 'string' && !isNaN(Number(value))) {
        sanitizedValue = Number(value)
      } else {
        errors.push({
          path,
          message: `Expected number, got ${typeof value}`,
          code: 'INVALID_TYPE',
          expectedType: 'number',
          actualType: typeof value,
          value
        })
        return { isValid: false, errors }
      }
    }

    const numValue = sanitizedValue as number

    // NaN check
    if (isNaN(numValue)) {
      errors.push({
        path,
        message: `Value is NaN`,
        code: 'NAN',
        value
      })
      return { isValid: false, errors }
    }

    // Range validation
    if (schema.minimum !== undefined && numValue < schema.minimum) {
      errors.push({
        path,
        message: `Number below minimum (min: ${schema.minimum}, actual: ${numValue})`,
        code: 'BELOW_MINIMUM',
        value
      })
    }

    if (schema.maximum !== undefined && numValue > schema.maximum) {
      errors.push({
        path,
        message: `Number above maximum (max: ${schema.maximum}, actual: ${numValue})`,
        code: 'ABOVE_MAXIMUM',
        value
      })
    }

    // Multiple validation
    if (schema.multipleOf !== undefined && numValue % schema.multipleOf !== 0) {
      errors.push({
        path,
        message: `Number not a multiple of ${schema.multipleOf}`,
        code: 'NOT_MULTIPLE',
        value
      })
    }

    return { isValid: errors.length === 0, errors, sanitizedValue }
  }

  private validateBoolean(value: any, schema: BooleanSchema, path: string): ValidationResult {
    const errors: ValidationError[] = []
    let sanitizedValue = value

    if (typeof value !== 'boolean') {
      // Try to convert
      if (value === 'true' || value === '1' || value === 1) {
        sanitizedValue = true
      } else if (value === 'false' || value === '0' || value === 0) {
        sanitizedValue = false
      } else {
        errors.push({
          path,
          message: `Expected boolean, got ${typeof value}`,
          code: 'INVALID_TYPE',
          expectedType: 'boolean',
          actualType: typeof value,
          value
        })
      }
    }

    return { isValid: errors.length === 0, errors, sanitizedValue }
  }

  private validateArray(value: any, schema: ArraySchema, path: string): ValidationResult {
    const errors: ValidationError[] = []
    let sanitizedValue = value

    if (!Array.isArray(value)) {
      errors.push({
        path,
        message: `Expected array, got ${typeof value}`,
        code: 'INVALID_TYPE',
        expectedType: 'array',
        actualType: typeof value,
        value
      })
      return { isValid: false, errors }
    }

    const arrValue = value as any[]

    // Length validation
    if (schema.minItems !== undefined && arrValue.length < schema.minItems) {
      errors.push({
        path,
        message: `Array too short (min: ${schema.minItems}, actual: ${arrValue.length})`,
        code: 'MIN_ITEMS',
        value
      })
    }

    if (schema.maxItems !== undefined && arrValue.length > schema.maxItems) {
      errors.push({
        path,
        message: `Array too long (max: ${schema.maxItems}, actual: ${arrValue.length})`,
        code: 'MAX_ITEMS',
        value
      })
    }

    // Validate each item
    const sanitizedItems: any[] = []
    arrValue.forEach((item, index) => {
      const itemResult = this.validate(item, schema.items, `${path}[${index}]`)
      if (!itemResult.isValid) {
        errors.push(...itemResult.errors)
      } else {
        sanitizedItems.push(itemResult.sanitizedValue)
      }
    })

    if (errors.length === 0) {
      sanitizedValue = sanitizedItems
    }

    return { isValid: errors.length === 0, errors, sanitizedValue }
  }

  private validateObject(value: any, schema: ObjectSchema, path: string): ValidationResult {
    const errors: ValidationError[] = []
    let sanitizedValue = value

    if (typeof value !== 'object' || value === null || Array.isArray(value)) {
      errors.push({
        path,
        message: `Expected object, got ${Array.isArray(value) ? 'array' : typeof value}`,
        code: 'INVALID_TYPE',
        expectedType: 'object',
        actualType: Array.isArray(value) ? 'array' : typeof value,
        value
      })
      return { isValid: false, errors }
    }

    const objValue = value as Record<string, any>
    const sanitizedObj: Record<string, any> = {}

    // Validate required properties
    if (schema.requiredProps) {
      for (const requiredProp of schema.requiredProps) {
        if (!(requiredProp in objValue)) {
          errors.push({
            path: `${path}.${requiredProp}`,
            message: `Required property missing: ${requiredProp}`,
            code: 'REQUIRED_PROPERTY',
            value: undefined
          })
        }
      }
    }

    // Validate each property
    for (const [propName, propSchema] of Object.entries(schema.properties)) {
      const propPath = path ? `${path}.${propName}` : propName
      const propValue = objValue[propName]
      
      const propResult = this.validate(propValue, propSchema, propPath)
      if (!propResult.isValid) {
        errors.push(...propResult.errors)
      } else if (propResult.sanitizedValue !== undefined) {
        sanitizedObj[propName] = propResult.sanitizedValue
      }
    }

    // Check for additional properties
    if (!schema.additionalProperties) {
      const allowedProps = new Set(Object.keys(schema.properties))
      for (const propName of Object.keys(objValue)) {
        if (!allowedProps.has(propName)) {
          errors.push({
            path: `${path}.${propName}`,
            message: `Additional property not allowed: ${propName}`,
            code: 'ADDITIONAL_PROPERTY',
            value: objValue[propName]
          })
        }
      }
    } else {
      // Include additional properties in sanitized result
      for (const [propName, propValue] of Object.entries(objValue)) {
        if (!(propName in schema.properties)) {
          sanitizedObj[propName] = propValue
        }
      }
    }

    if (errors.length === 0) {
      sanitizedValue = sanitizedObj
    }

    return { isValid: errors.length === 0, errors, sanitizedValue }
  }

  private validateUnion(value: any, schema: UnionSchema, path: string): ValidationResult {
    const allErrors: ValidationError[] = []
    
    // Try each schema in the union
    for (const unionSchema of schema.schemas) {
      const result = this.validate(value, unionSchema, path)
      if (result.isValid) {
        return result // Return first successful validation
      }
      allErrors.push(...result.errors)
    }

    // If no schema matched, return combined errors
    return {
      isValid: false,
      errors: [{
        path,
        message: `Value does not match any of the union types`,
        code: 'UNION_MISMATCH',
        value
      }]
    }
  }
}

// Global validator instance
export const validator = new SchemaValidator()

/** Tool schema definitions */
export const TOOL_SCHEMAS: Record<string, ToolDefinition> = {
  // MCP Business Tools
  prospects_search: {
    name: 'prospects_search',
    description: 'Search business prospects with filtering',
    inputSchema: obj({
      query: str({ description: 'Search query', maxLength: 500 }),
      filters: obj({
        industry: str({ required: false }),
        size: str({ enum: ['startup', 'small', 'medium', 'large'], required: false }),
        location: str({ required: false })
      }, { required: false })
    }),
    outputSchema: obj({
      results: arr(obj({
        id: str({ required: true }),
        name: str({ required: true }),
        industry: str({ required: true }),
        size: str({ required: true }),
        score: num({ minimum: 0, maximum: 1 })
      })),
      total: num({ minimum: 0 }),
      executionTimeMs: num({ minimum: 0 })
    })
  },

  // MCP Research Tools
  arxiv_search: {
    name: 'arxiv_search',
    description: 'Search academic papers on ArXiv',
    inputSchema: obj({
      query: str({ description: 'Research query', maxLength: 200, required: true }),
      max_results: num({ minimum: 1, maximum: 100, required: false })
    }),
    outputSchema: obj({
      papers: arr(obj({
        id: str({ required: true }),
        title: str({ required: true }),
        authors: arr(str()),
        abstract: str({ required: true }),
        published: str({ required: true }),
        url: str({ required: true })
      })),
      query: str({ required: true }),
      total_found: num({ minimum: 0 })
    })
  },

  // MCP Context Tools  
  context_search: {
    name: 'context_search',
    description: 'Search contextual information',
    inputSchema: obj({
      query: str({ description: 'Context search query', maxLength: 300, required: true }),
      limit: num({ minimum: 1, maximum: 50, required: false }),
      filters: obj({
        type: str({ enum: ['document', 'conversation', 'code'], required: false }),
        date_range: obj({
          start: str({ required: false }),
          end: str({ required: false })
        }, { required: false })
      }, { required: false })
    }),
    outputSchema: obj({
      results: arr(obj({
        id: str({ required: true }),
        content: str({ required: true }),
        type: str({ required: true }),
        relevance: num({ minimum: 0, maximum: 1 }),
        metadata: obj({}, { additionalProperties: true, required: false })
      })),
      total: num({ minimum: 0 }),
      query: str({ required: true })
    })
  },

  // Standard response schema for errors
  error: {
    name: 'error',
    description: 'Standard error response',
    inputSchema: obj({}),
    outputSchema: obj({
      success: bool({ required: true }),
      error_code: str({ required: true }),
      message: str({ required: true }),
      details: obj({}, { additionalProperties: true, required: false }),
      timestamp: str({ required: true }),
      execution_id: str({ required: false })
    })
  }
}

/**
 * Validate tool input against its schema
 */
export function validateToolInput(toolName: string, input: any): ValidationResult {
  const toolDef = TOOL_SCHEMAS[toolName]
  if (!toolDef) {
    return {
      isValid: false,
      errors: [{
        path: '',
        message: `Unknown tool: ${toolName}`,
        code: 'UNKNOWN_TOOL',
        value: toolName
      }]
    }
  }

  return validator.validate(input, toolDef.inputSchema)
}

/**
 * Validate tool output against its schema
 */
export function validateToolOutput(toolName: string, output: any): ValidationResult {
  const toolDef = TOOL_SCHEMAS[toolName]
  if (!toolDef) {
    return {
      isValid: false,
      errors: [{
        path: '',
        message: `Unknown tool: ${toolName}`,
        code: 'UNKNOWN_TOOL',
        value: toolName
      }]
    }
  }

  return validator.validate(output, toolDef.outputSchema)
}

/**
 * Get tool definition by name
 */
export function getToolDefinition(toolName: string): ToolDefinition | null {
  return TOOL_SCHEMAS[toolName] || null
}

/**
 * Register a new tool schema
 */
export function registerToolSchema(toolDef: ToolDefinition): void {
  TOOL_SCHEMAS[toolDef.name] = toolDef
}