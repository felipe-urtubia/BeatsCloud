export type UploadStatus = 'pending' | 'uploading' | 'error' | 'complete';
export type UploadStatusAction = { type: 'start' | 'succeed' | 'fail' | 'reset' };
export function uploadStatusReducer(state: UploadStatus, action: UploadStatusAction): UploadStatus;
export function getUploadStatusLabel(status: UploadStatus, configuredMode: 'mock' | 'hybrid'): string;
