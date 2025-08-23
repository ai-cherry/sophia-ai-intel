/**
 * Sophia AI Tool I/O Schemas
 * Strict TypeScript validation schemas for all tool inputs and outputs
 * (TypeScript equivalent to Pydantic schemas)
 */

// Simple validation library implementation (lightweight alternative to zod)
type ValidationError = {
  field: string;
  message: string;
  value: any;
};

class ValidationResult<T> {
  constructor(
    public success: boolean,
    public data?: T,
    public errors: ValidationError[] = []
  ) {}
}

function validate<T>(schema: Schema<T>, data: any): ValidationResult<T> {
  const errors: ValidationError[] = [];
  const result = schema.validate(data, errors);
  
  if (errors.length > 0) {
    return new ValidationResult<T>(false, undefined, errors);
  }
  
  return new ValidationResult<T>(true, result);
}

interface Schema<T> {
  validate(data: any, errors: ValidationError[]): T;
}

// Basic schema types
class StringSchema implements Schema<string> {
  constructor(
    private options: {
      required?: boolean;
      minLength?: number;
      maxLength?: number;
      pattern?: RegExp;
      enum?: string[];
    } = {}
  ) {}

  validate(data: any, errors: ValidationError[]): string {
    if (this.options.required && (data === undefined || data === null)) {
      errors.push({ field: 'value', message: 'Required field', value: data });
      return '';
    }

    if (typeof data !== 'string') {
      errors.push({ field: 'value', message: 'Must be a string', value: data });
      return '';
    }

    if (this.options.minLength && data.length < this.options.minLength) {
      errors.push({ field: 'value', message: `Minimum length ${this.options.minLength}`, value: data });
    }

    if (this.options.maxLength && data.length > this.options.maxLength) {
      errors.push({ field: 'value', message: `Maximum length ${this.options.maxLength}`, value: data });
    }

    if (this.options.pattern && !this.options.pattern.test(data)) {
      errors.push({ field: 'value', message: 'Pattern mismatch', value: data });
    }

    if (this.options.enum && !this.options.enum.includes(data)) {
      errors.push({ field: 'value', message: `Must be one of: ${this.options.enum.join(', ')}`, value: data });
    }

    return data;
  }
}

class NumberSchema implements Schema<number> {
  constructor(
    private options: {
      required?: boolean;
      min?: number;
      max?: number;
      integer?: boolean;
    } = {}
  ) {}

  validate(data: any, errors: ValidationError[]): number {
    if (this.options.required && (data === undefined || data === null)) {
      errors.push({ field: 'value', message: 'Required field', value: data });
      return 0;
    }

    const num = Number(data);
    if (isNaN(num)) {
      errors.push({ field: 'value', message: 'Must be a number', value: data });
      return 0;
    }

    if (this.options.integer && !Number.isInteger(num)) {
      errors.push({ field: 'value', message: 'Must be an integer', value: data });
    }

    if (this.options.min !== undefined && num < this.options.min) {
      errors.push({ field: 'value', message: `Minimum value ${this.options.min}`, value: data });
    }

    if (this.options.max !== undefined && num > this.options.max) {
      errors.push({ field: 'value', message: `Maximum value ${this.options.max}`, value: data });
    }

    return num;
  }
}

class ObjectSchema<T> implements Schema<T> {
  constructor(private fields: Record<string, Schema<any>>) {}

  validate(data: any, errors: ValidationError[]): T {
    if (typeof data !== 'object' || data === null) {
      errors.push({ field: 'root', message: 'Must be an object', value: data });
      return {} as T;
    }

    const result: any = {};
    
    for (const [fieldName, fieldSchema] of Object.entries(this.fields)) {
      const fieldErrors: ValidationError[] = [];
      result[fieldName] = fieldSchema.validate(data[fieldName], fieldErrors);
      
      // Prefix field names with the current field
      fieldErrors.forEach(error => {
        error.field = `${fieldName}.${error.field}`;
        errors.push(error);
      });
    }

    return result as T;
  }
}

class ArraySchema<T> implements Schema<T[]> {
  constructor(
    private itemSchema: Schema<T>,
    private options: {
      minItems?: number;
      maxItems?: number;
      required?: boolean;
    } = {}
  ) {}

  validate(data: any, errors: ValidationError[]): T[] {
    if (this.options.required && (data === undefined || data === null)) {
      errors.push({ field: 'value', message: 'Required field', value: data });
      return [];
    }

    if (!Array.isArray(data)) {
      errors.push({ field: 'value', message: 'Must be an array', value: data });
      return [];
    }

    if (this.options.minItems && data.length < this.options.minItems) {
      errors.push({ field: 'value', message: `Minimum ${this.options.minItems} items`, value: data });
    }

    if (this.options.maxItems && data.length > this.options.maxItems) {
      errors.push({ field: 'value', message: `Maximum ${this.options.maxItems} items`, value: data });
    }

    const result: T[] = [];
    data.forEach((item, index) => {
      const itemErrors: ValidationError[] = [];
      const validatedItem = this.itemSchema.validate(item, itemErrors);
      
      itemErrors.forEach(error => {
        error.field = `[${index}].${error.field}`;
        errors.push(error);
      });
      
      result.push(validatedItem);
    });

    return result;
  }
}

// Helper functions for creating schemas
const str = (options?: Parameters<typeof StringSchema>[0]) => new StringSchema(options);
const num = (options?: Parameters<typeof NumberSchema>[0]) => new NumberSchema(options);
const obj = <T>(fields: Record<string, Schema<any>>) => new ObjectSchema<T>(fields);
const arr = <T>(itemSchema: Schema<T>, options?: Parameters<typeof ArraySchema<T>>[0]) => new ArraySchema(itemSchema, options);

// Common tool schemas
export interface McpToolRequest {
  service: string;
  method: string;
  params: Record<string, any>;
  timeout?: number;
  retries?: number;
  idempotencyKey?: string;
}

export interface McpToolResponse {
  success: boolean;
  data?: any;
  error?: string;
  service: string;
  method: string;
  duration: number;
  cached: boolean;
}

export interface RetrievalRequest {
  query: string;
  maxResults?: number;
  threshold?: number;
  includeMetadata?: boolean;
  filters?: Record<string, any>;
}

export interface RetrievalResponse {
  results: Array<{
    id: string;
    content: string;
    score: number;
    metadata?: Record<string, any>;
  }>;
  totalResults: number;
  query: string;
  processingTime: number;
}

export interface WebResearchRequest {
  query: string;
  maxResults?: number;
  domains?: string[];
  timeRange?: 'day' | 'week' | 'month' | 'year' | 'all';
  language?: string;
}

export interface WebResearchResponse {
  results: Array<{
    title: string;
    url: string;
    snippet: string;
    publishedAt?: string;
    domain: string;
    relevanceScore: number;
  }>;
  query: string;
  totalFound: number;
  searchTime: number;
}

export interface PlanningRequest {
  query: string;
  context: string;
  constraints: string[];
  maxSteps?: number;
  complexity?: 'low' | 'medium' | 'high';
  timeframe?: string;
}

export interface PlanningResponse {
  planId: string;
  steps: Array<{
    id: string;
    type: string;
    description: string;
    estimatedTime: string;
    dependencies: string[];
  }>;
  estimatedTotalTime: string;
  confidence: number;
  alternatives?: string[];
}

export interface SynthesisRequest {
  sources: Array<{
    type: 'retrieval' | 'web' | 'mcp' | 'planning';
    content: any;
    weight?: number;
  }>;
  outputFormat?: 'summary' | 'detailed' | 'structured';
  maxLength?: number;
  includeReferences?: boolean;
}

export interface SynthesisResponse {
  synthesis: string;
  confidence: number;
  sources: Array<{
    type: string;
    used: boolean;
    weight: number;
  }>;
  keyPoints: string[];
  references?: string[];
}

// Schema definitions
export const McpToolRequestSchema = obj<McpToolRequest>({
  service: str({ required: true, minLength: 1, maxLength: 100 }),
  method: str({ required: true, minLength: 1, maxLength: 100 }),
  params: new ObjectSchema({}),
  timeout: num({ min: 1000, max: 300000, integer: true }),
  retries: num({ min: 0, max: 5, integer: true }),
  idempotencyKey: str({ maxLength: 255 }),
});

export const McpToolResponseSchema = obj<McpToolResponse>({
  success: new Schema<boolean>() {
    validate(data: any, errors: ValidationError[]): boolean {
      if (typeof data !== 'boolean') {
        errors.push({ field: 'value', message: 'Must be a boolean', value: data });
        return false;
      }
      return data;
    }
  },
  data: new Schema<any>() {
    validate(data: any): any { return data; }
  },
  error: str(),
  service: str({ required: true }),
  method: str({ required: true }),
  duration: num({ required: true, min: 0 }),
  cached: new Schema<boolean>() {
    validate(data: any, errors: ValidationError[]): boolean {
      if (typeof data !== 'boolean') {
        errors.push({ field: 'value', message: 'Must be a boolean', value: data });
        return false;
      }
      return data;
    }
  },
});

export const RetrievalRequestSchema = obj<RetrievalRequest>({
  query: str({ required: true, minLength: 1, maxLength: 1000 }),
  maxResults: num({ min: 1, max: 100, integer: true }),
  threshold: num({ min: 0, max: 1 }),
  includeMetadata: new Schema<boolean>() {
    validate(data: any, errors: ValidationError[]): boolean {
      if (data !== undefined && typeof data !== 'boolean') {
        errors.push({ field: 'value', message: 'Must be a boolean', value: data });
        return false;
      }
      return data ?? false;
    }
  },
  filters: new ObjectSchema({}),
});

export const RetrievalResponseSchema = obj<RetrievalResponse>({
  results: arr(obj({
    id: str({ required: true }),
    content: str({ required: true }),
    score: num({ required: true, min: 0, max: 1 }),
    metadata: new ObjectSchema({}),
  }), { required: true }),
  totalResults: num({ required: true, min: 0, integer: true }),
  query: str({ required: true }),
  processingTime: num({ required: true, min: 0 }),
});

export const WebResearchRequestSchema = obj<WebResearchRequest>({
  query: str({ required: true, minLength: 1, maxLength: 500 }),
  maxResults: num({ min: 1, max: 50, integer: true }),
  domains: arr(str({ pattern: /^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/ })),
  timeRange: str({ enum: ['day', 'week', 'month', 'year', 'all'] }),
  language: str({ minLength: 2, maxLength: 5 }),
});

export const WebResearchResponseSchema = obj<WebResearchResponse>({
  results: arr(obj({
    title: str({ required: true }),
    url: str({ required: true, pattern: /^https?:\/\/.+/ }),
    snippet: str({ required: true }),
    publishedAt: str(),
    domain: str({ required: true }),
    relevanceScore: num({ required: true, min: 0, max: 1 }),
  }), { required: true }),
  query: str({ required: true }),
  totalFound: num({ required: true, min: 0, integer: true }),
  searchTime: num({ required: true, min: 0 }),
});

export const PlanningRequestSchema = obj<PlanningRequest>({
  query: str({ required: true, minLength: 1, maxLength: 2000 }),
  context: str({ required: true, maxLength: 5000 }),
  constraints: arr(str({ maxLength: 500 }), { required: true }),
  maxSteps: num({ min: 1, max: 20, integer: true }),
  complexity: str({ enum: ['low', 'medium', 'high'] }),
  timeframe: str({ maxLength: 100 }),
});

export const PlanningResponseSchema = obj<PlanningResponse>({
  planId: str({ required: true, pattern: /^[a-zA-Z0-9_-]+$/ }),
  steps: arr(obj({
    id: str({ required: true }),
    type: str({ required: true }),
    description: str({ required: true }),
    estimatedTime: str({ required: true }),
    dependencies: arr(str(), { required: true }),
  }), { required: true, minItems: 1, maxItems: 20 }),
  estimatedTotalTime: str({ required: true }),
  confidence: num({ required: true, min: 0, max: 1 }),
  alternatives: arr(str()),
});

export const SynthesisRequestSchema = obj<SynthesisRequest>({
  sources: arr(obj({
    type: str({ required: true, enum: ['retrieval', 'web', 'mcp', 'planning'] }),
    content: new Schema<any>() { validate(data: any): any { return data; } },
    weight: num({ min: 0, max: 1 }),
  }), { required: true, minItems: 1, maxItems: 10 }),
  outputFormat: str({ enum: ['summary', 'detailed', 'structured'] }),
  maxLength: num({ min: 100, max: 10000, integer: true }),
  includeReferences: new Schema<boolean>() {
    validate(data: any, errors: ValidationError[]): boolean {
      if (data !== undefined && typeof data !== 'boolean') {
        errors.push({ field: 'value', message: 'Must be a boolean', value: data });
        return false;
      }
      return data ?? false;
    }
  },
});

export const SynthesisResponseSchema = obj<SynthesisResponse>({
  synthesis: str({ required: true, minLength: 1 }),
  confidence: num({ required: true, min: 0, max: 1 }),
  sources: arr(obj({
    type: str({ required: true }),
    used: new Schema<boolean>() {
      validate(data: any, errors: ValidationError[]): boolean {
        return typeof data === 'boolean' ? data : false;
      }
    },
    weight: num({ required: true, min: 0, max: 1 }),
  }), { required: true }),
  keyPoints: arr(str({ minLength: 1 }), { required: true }),
  references: arr(str({ minLength: 1 })),
});

// Validation utilities
export class ToolValidator {
  /**
   * Validate MCP tool request
   */
  static validateMcpRequest(data: any): ValidationResult<McpToolRequest> {
    return validate(McpToolRequestSchema, data);
  }

  /**
   * Validate MCP tool response
   */
  static validateMcpResponse(data: any): ValidationResult<McpToolResponse> {
    return validate(McpToolResponseSchema, data);
  }

  /**
   * Validate retrieval request
   */
  static validateRetrievalRequest(data: any): ValidationResult<RetrievalRequest> {
    return validate(RetrievalRequestSchema, data);
  }

  /**
   * Validate retrieval response
   */
  static validateRetrievalResponse(data: any): ValidationResult<RetrievalResponse> {
    return validate(RetrievalResponseSchema, data);
  }

  /**
   * Validate web research request
   */
  static validateWebResearchRequest(data: any): ValidationResult<WebResearchRequest> {
    return validate(WebResearchRequestSchema, data);
  }

  /**
   * Validate web research response
   */
  static validateWebResearchResponse(data: any): ValidationResult<WebResearchResponse> {
    return validate(WebResearchResponseSchema, data);
  }

  /**
   * Validate planning request
   */
  static validatePlanningRequest(data: any): ValidationResult<PlanningRequest> {
    return validate(PlanningRequestSchema, data);
  }

  /**
   * Validate planning response
   */
  static validatePlanningResponse(data: any): ValidationResult<PlanningResponse> {
    return validate(PlanningResponseSchema, data);
  }

  /**
   * Validate synthesis request
   */
  static validateSynthesisRequest(data: any): ValidationResult<SynthesisRequest> {
    return validate(SynthesisRequestSchema, data);
  }

  /**
   * Validate synthesis response
   */
  static validateSynthesisResponse(data: any): ValidationResult<SynthesisResponse> {
    return validate(SynthesisResponseSchema, data);
  }

  /**
   * Generic validation helper
   */
  static validate<T>(schema: Schema<T>, data: any): ValidationResult<T> {
    return validate(schema, data);
  }
}

/**
 * Decorator for validating function inputs and outputs
 */
export function validateIO<TInput, TOutput>(
  inputSchema: Schema<TInput>,
  outputSchema: Schema<TOutput>
) {
  return function (target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      // Validate input
      if (args.length > 0) {
        const inputValidation = validate(inputSchema, args[0]);
        if (!inputValidation.success) {
          throw new Error(`Input validation failed: ${JSON.stringify(inputValidation.errors)}`);
        }
        args[0] = inputValidation.data;
      }

      // Execute method
      const result = await method.apply(this, args);

      // Validate output
      const outputValidation = validate(outputSchema, result);
      if (!outputValidation.success) {
        console.error(`Output validation failed for ${propertyName}:`, outputValidation.errors);
        // Don't throw on output validation failure, just log
      }

      return outputValidation.data || result;
    };
  };
}

// Export validation utilities
export { validate, ValidationResult, ValidationError };