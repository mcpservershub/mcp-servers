import { z } from 'zod';

export const NavigateSchema = z.object({
  url: z.string().url('Invalid URL format'),
  waitUntil: z.enum(['load', 'domcontentloaded', 'networkidle0', 'networkidle2']).optional().default('networkidle2'),
  output_file: z.string().optional()
});

export const ScreenshotSchema = z.object({
  selector: z.string().optional(),
  fullPage: z.boolean().optional().default(false),
  format: z.enum(['png', 'jpeg', 'webp']).optional().default('png'),
  quality: z.number().min(0).max(100).optional(),
  output_file: z.string().optional()
});

export const ClickSchema = z.object({
  selector: z.string().min(1, 'Selector is required'),
  clickCount: z.number().positive().optional().default(1),
  delay: z.number().nonnegative().optional().default(0)
});

export const TypeSchema = z.object({
  selector: z.string().min(1, 'Selector is required'),
  text: z.string().min(1, 'Text is required'),
  delay: z.number().nonnegative().optional().default(0),
  clear: z.boolean().optional().default(false)
});

export const WaitForSelectorSchema = z.object({
  selector: z.string().min(1, 'Selector is required'),
  timeout: z.number().positive().optional().default(30000),
  visible: z.boolean().optional().default(true),
  hidden: z.boolean().optional().default(false)
});

export const EvaluateSchema = z.object({
  script: z.string().min(1, 'Script is required'),
  args: z.array(z.unknown()).optional().default([]),
  output_file: z.string().optional()
});

export const GetContentSchema = z.object({
  selector: z.string().optional(),
  type: z.enum(['text', 'html', 'value']).optional().default('text'),
  output_file: z.string().optional()
});

export const ScrollSchema = z.object({
  x: z.number().optional().default(0),
  y: z.number().optional().default(0),
  smooth: z.boolean().optional().default(true)
});

export const SetViewportSchema = z.object({
  width: z.number().positive().min(1),
  height: z.number().positive().min(1),
  deviceScaleFactor: z.number().positive().optional().default(1),
  isMobile: z.boolean().optional().default(false),
  hasTouch: z.boolean().optional().default(false)
});

export const PdfSchema = z.object({
  path: z.string().optional(),
  format: z.enum(['Letter', 'Legal', 'Tabloid', 'Ledger', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6']).optional(),
  width: z.string().optional(),
  height: z.string().optional(),
  landscape: z.boolean().optional().default(false),
  margin: z.object({
    top: z.string().optional(),
    right: z.string().optional(),
    bottom: z.string().optional(),
    left: z.string().optional()
  }).optional(),
  printBackground: z.boolean().optional().default(false),
  scale: z.number().min(0.1).max(2).optional().default(1),
  output_file: z.string().optional()
});

export const FillFormSchema = z.object({
  fields: z.record(z.string(), z.string()).refine(
    (fields) => Object.keys(fields).length > 0,
    { message: 'At least one field is required' }
  ),
  output_file: z.string().optional()
});

export const ExtractLinksSchema = z.object({
  selector: z.string().optional().default('a'),
  includeText: z.boolean().optional().default(true),
  output_file: z.string().optional()
});

export type NavigateInput = z.infer<typeof NavigateSchema>;
export type ScreenshotInput = z.infer<typeof ScreenshotSchema>;
export type ClickInput = z.infer<typeof ClickSchema>;
export type TypeInput = z.infer<typeof TypeSchema>;
export type WaitForSelectorInput = z.infer<typeof WaitForSelectorSchema>;
export type EvaluateInput = z.infer<typeof EvaluateSchema>;
export type GetContentInput = z.infer<typeof GetContentSchema>;
export type ScrollInput = z.infer<typeof ScrollSchema>;
export type SetViewportInput = z.infer<typeof SetViewportSchema>;
export type PdfInput = z.infer<typeof PdfSchema>;
export type FillFormInput = z.infer<typeof FillFormSchema>;
export type ExtractLinksInput = z.infer<typeof ExtractLinksSchema>;