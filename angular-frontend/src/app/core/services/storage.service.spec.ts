/**
 * StorageService Tests
 * Comprehensive tests for localStorage wrapper with SSR support and error handling
 */

import { TestBed } from '@angular/core/testing';
import { PLATFORM_ID } from '@angular/core';
import { StorageService } from './storage.service';

describe('StorageService', () => {
  let service: StorageService;
  let localStorageSpy: jasmine.SpyObj<Storage>;

  beforeEach(() => {
    // Create localStorage spy
    localStorageSpy = jasmine.createSpyObj('localStorage', [
      'getItem',
      'setItem',
      'removeItem',
      'clear'
    ]);

    // Replace localStorage with spy
    Object.defineProperty(window, 'localStorage', {
      value: localStorageSpy,
      writable: true,
      configurable: true
    });
  });

  afterEach(() => {
    // Clean up spy
    localStorageSpy.getItem.calls.reset();
    localStorageSpy.setItem.calls.reset();
    localStorageSpy.removeItem.calls.reset();
    localStorageSpy.clear.calls.reset();
  });

  describe('Browser Platform', () => {
    beforeEach(() => {
      TestBed.configureTestingModule({
        providers: [
          StorageService,
          { provide: PLATFORM_ID, useValue: 'browser' }
        ]
      });
      service = TestBed.inject(StorageService);
    });

    describe('Service Initialization', () => {
      it('should be created', () => {
        expect(service).toBeTruthy();
      });

      it('should detect browser platform', () => {
        localStorageSpy.setItem.and.returnValue(undefined);
        localStorageSpy.removeItem.and.returnValue(undefined);

        expect(service.isAvailable()).toBe(true);
      });
    });

    describe('getItem()', () => {
      it('should retrieve item from localStorage', () => {
        localStorageSpy.getItem.and.returnValue('test-value');

        const result = service.getItem('test-key');

        expect(localStorageSpy.getItem).toHaveBeenCalledWith('test-key');
        expect(result).toBe('test-value');
      });

      it('should return null for non-existent key', () => {
        localStorageSpy.getItem.and.returnValue(null);

        const result = service.getItem('non-existent-key');

        expect(result).toBeNull();
      });

      it('should handle localStorage errors gracefully', () => {
        localStorageSpy.getItem.and.throwError('localStorage error');
        spyOn(console, 'warn');

        const result = service.getItem('error-key');

        expect(result).toBeNull();
        expect(console.warn).toHaveBeenCalled();
      });

      it('should handle empty string values', () => {
        localStorageSpy.getItem.and.returnValue('');

        const result = service.getItem('empty-key');

        expect(result).toBe('');
      });

      it('should handle special characters in keys', () => {
        localStorageSpy.getItem.and.returnValue('value');

        const result = service.getItem('key-with-special-chars!@#$%');

        expect(localStorageSpy.getItem).toHaveBeenCalledWith('key-with-special-chars!@#$%');
        expect(result).toBe('value');
      });
    });

    describe('setItem()', () => {
      it('should store item in localStorage', () => {
        localStorageSpy.setItem.and.returnValue(undefined);

        const result = service.setItem('test-key', 'test-value');

        expect(localStorageSpy.setItem).toHaveBeenCalledWith('test-key', 'test-value');
        expect(result).toBe(true);
      });

      it('should return false on localStorage error', () => {
        localStorageSpy.setItem.and.throwError('Storage quota exceeded');
        spyOn(console, 'warn');

        const result = service.setItem('quota-key', 'large-value');

        expect(result).toBe(false);
        expect(console.warn).toHaveBeenCalled();
      });

      it('should handle empty string values', () => {
        localStorageSpy.setItem.and.returnValue(undefined);

        const result = service.setItem('empty-key', '');

        expect(localStorageSpy.setItem).toHaveBeenCalledWith('empty-key', '');
        expect(result).toBe(true);
      });

      it('should handle overwriting existing values', () => {
        localStorageSpy.setItem.and.returnValue(undefined);

        service.setItem('existing-key', 'old-value');
        const result = service.setItem('existing-key', 'new-value');

        expect(localStorageSpy.setItem).toHaveBeenCalledWith('existing-key', 'new-value');
        expect(result).toBe(true);
      });

      it('should handle special characters in values', () => {
        localStorageSpy.setItem.and.returnValue(undefined);

        const specialValue = 'value with \n newlines \t tabs "quotes"';
        const result = service.setItem('special-key', specialValue);

        expect(localStorageSpy.setItem).toHaveBeenCalledWith('special-key', specialValue);
        expect(result).toBe(true);
      });
    });

    describe('removeItem()', () => {
      it('should remove item from localStorage', () => {
        localStorageSpy.removeItem.and.returnValue(undefined);

        const result = service.removeItem('test-key');

        expect(localStorageSpy.removeItem).toHaveBeenCalledWith('test-key');
        expect(result).toBe(true);
      });

      it('should return false on localStorage error', () => {
        localStorageSpy.removeItem.and.throwError('localStorage error');
        spyOn(console, 'warn');

        const result = service.removeItem('error-key');

        expect(result).toBe(false);
        expect(console.warn).toHaveBeenCalled();
      });

      it('should handle removing non-existent keys', () => {
        localStorageSpy.removeItem.and.returnValue(undefined);

        const result = service.removeItem('non-existent-key');

        expect(localStorageSpy.removeItem).toHaveBeenCalledWith('non-existent-key');
        expect(result).toBe(true);
      });
    });

    describe('clear()', () => {
      it('should clear all localStorage', () => {
        localStorageSpy.clear.and.returnValue(undefined);

        const result = service.clear();

        expect(localStorageSpy.clear).toHaveBeenCalled();
        expect(result).toBe(true);
      });

      it('should return false on localStorage error', () => {
        localStorageSpy.clear.and.throwError('localStorage error');
        spyOn(console, 'warn');

        const result = service.clear();

        expect(result).toBe(false);
        expect(console.warn).toHaveBeenCalled();
      });
    });

    describe('isAvailable()', () => {
      it('should return true when localStorage is available', () => {
        localStorageSpy.setItem.and.returnValue(undefined);
        localStorageSpy.removeItem.and.returnValue(undefined);

        const result = service.isAvailable();

        expect(result).toBe(true);
        expect(localStorageSpy.setItem).toHaveBeenCalledWith('__localStorage_test__', 'test');
        expect(localStorageSpy.removeItem).toHaveBeenCalledWith('__localStorage_test__');
      });

      it('should return false when localStorage throws error', () => {
        localStorageSpy.setItem.and.throwError('localStorage not available');

        const result = service.isAvailable();

        expect(result).toBe(false);
      });

      it('should return false when localStorage is disabled', () => {
        localStorageSpy.setItem.and.throwError('SecurityError');

        const result = service.isAvailable();

        expect(result).toBe(false);
      });
    });

    describe('getJson()', () => {
      it('should parse and return JSON object', () => {
        const testObject = { name: 'Test', value: 123 };
        localStorageSpy.getItem.and.returnValue(JSON.stringify(testObject));

        const result = service.getJson<typeof testObject>('json-key');

        expect(result).toEqual(testObject);
      });

      it('should parse and return JSON array', () => {
        const testArray = [1, 2, 3, 4, 5];
        localStorageSpy.getItem.and.returnValue(JSON.stringify(testArray));

        const result = service.getJson<typeof testArray>('array-key');

        expect(result).toEqual(testArray);
      });

      it('should return null for non-existent key', () => {
        localStorageSpy.getItem.and.returnValue(null);

        const result = service.getJson('non-existent-key');

        expect(result).toBeNull();
      });

      it('should return null for invalid JSON', () => {
        localStorageSpy.getItem.and.returnValue('invalid json {{{');
        localStorageSpy.removeItem.and.returnValue(undefined);
        spyOn(console, 'warn');

        const result = service.getJson('invalid-json-key');

        expect(result).toBeNull();
        expect(console.warn).toHaveBeenCalled();
        expect(localStorageSpy.removeItem).toHaveBeenCalledWith('invalid-json-key');
      });

      it('should handle complex nested objects', () => {
        const complex = {
          user: { name: 'Test', settings: { theme: 'dark', lang: 'en' } },
          data: [{ id: 1 }, { id: 2 }]
        };
        localStorageSpy.getItem.and.returnValue(JSON.stringify(complex));

        const result = service.getJson<typeof complex>('complex-key');

        expect(result).toEqual(complex);
      });

      it('should handle JSON with null values', () => {
        const withNull = { name: 'Test', value: null };
        localStorageSpy.getItem.and.returnValue(JSON.stringify(withNull));

        const result = service.getJson<typeof withNull>('null-key');

        expect(result).toEqual(withNull);
      });

      it('should handle JSON with boolean values', () => {
        const withBool = { enabled: true, disabled: false };
        localStorageSpy.getItem.and.returnValue(JSON.stringify(withBool));

        const result = service.getJson<typeof withBool>('bool-key');

        expect(result).toEqual(withBool);
      });
    });

    describe('setJson()', () => {
      it('should stringify and store JSON object', () => {
        const testObject = { name: 'Test', value: 123 };
        localStorageSpy.setItem.and.returnValue(undefined);

        const result = service.setJson('json-key', testObject);

        expect(localStorageSpy.setItem).toHaveBeenCalledWith(
          'json-key',
          JSON.stringify(testObject)
        );
        expect(result).toBe(true);
      });

      it('should stringify and store JSON array', () => {
        const testArray = [1, 2, 3, 4, 5];
        localStorageSpy.setItem.and.returnValue(undefined);

        const result = service.setJson('array-key', testArray);

        expect(localStorageSpy.setItem).toHaveBeenCalledWith(
          'array-key',
          JSON.stringify(testArray)
        );
        expect(result).toBe(true);
      });

      it('should return false on stringify error', () => {
        const circular: { ref?: unknown } = {};
        circular.ref = circular; // Create circular reference
        spyOn(console, 'warn');

        const result = service.setJson('circular-key', circular);

        expect(result).toBe(false);
        expect(console.warn).toHaveBeenCalled();
      });

      it('should handle complex nested objects', () => {
        const complex = {
          user: { name: 'Test', settings: { theme: 'dark' } },
          data: [{ id: 1 }]
        };
        localStorageSpy.setItem.and.returnValue(undefined);

        const result = service.setJson('complex-key', complex);

        expect(result).toBe(true);
      });

      it('should handle JSON with null values', () => {
        const withNull = { name: 'Test', value: null };
        localStorageSpy.setItem.and.returnValue(undefined);

        const result = service.setJson('null-key', withNull);

        expect(result).toBe(true);
      });

      it('should return false when localStorage fails', () => {
        localStorageSpy.setItem.and.throwError('Storage quota exceeded');

        const result = service.setJson('quota-key', { large: 'data' });

        expect(result).toBe(false);
      });
    });

    describe('Edge Cases', () => {
      it('should handle rapid consecutive operations', () => {
        localStorageSpy.setItem.and.returnValue(undefined);
        localStorageSpy.getItem.and.returnValue('value');

        for (let i = 0; i < 100; i++) {
          service.setItem(`key-${i}`, `value-${i}`);
          service.getItem(`key-${i}`);
        }

        expect(localStorageSpy.setItem).toHaveBeenCalledTimes(100);
        expect(localStorageSpy.getItem).toHaveBeenCalledTimes(100);
      });

      it('should handle Unicode characters', () => {
        localStorageSpy.setItem.and.returnValue(undefined);

        const unicode = '你好 مرحبا';
        const result = service.setItem('unicode-key', unicode);

        expect(result).toBe(true);
        expect(localStorageSpy.setItem).toHaveBeenCalledWith('unicode-key', unicode);
      });

      it('should handle very long keys', () => {
        localStorageSpy.setItem.and.returnValue(undefined);

        const longKey = 'a'.repeat(1000);
        const result = service.setItem(longKey, 'value');

        expect(result).toBe(true);
      });

      it('should handle empty key', () => {
        localStorageSpy.setItem.and.returnValue(undefined);

        const result = service.setItem('', 'value');

        expect(localStorageSpy.setItem).toHaveBeenCalledWith('', 'value');
        expect(result).toBe(true);
      });
    });
  });

  describe('Server Platform (SSR)', () => {
    beforeEach(() => {
      TestBed.configureTestingModule({
        providers: [
          StorageService,
          { provide: PLATFORM_ID, useValue: 'server' }
        ]
      });
      service = TestBed.inject(StorageService);
    });

    it('should be created on server', () => {
      expect(service).toBeTruthy();
    });

    it('should return null for getItem on server', () => {
      const result = service.getItem('test-key');

      expect(result).toBeNull();
      expect(localStorageSpy.getItem).not.toHaveBeenCalled();
    });

    it('should return false for setItem on server', () => {
      const result = service.setItem('test-key', 'value');

      expect(result).toBe(false);
      expect(localStorageSpy.setItem).not.toHaveBeenCalled();
    });

    it('should return false for removeItem on server', () => {
      const result = service.removeItem('test-key');

      expect(result).toBe(false);
      expect(localStorageSpy.removeItem).not.toHaveBeenCalled();
    });

    it('should return false for clear on server', () => {
      const result = service.clear();

      expect(result).toBe(false);
      expect(localStorageSpy.clear).not.toHaveBeenCalled();
    });

    it('should return false for isAvailable on server', () => {
      const result = service.isAvailable();

      expect(result).toBe(false);
    });

    it('should return null for getJson on server', () => {
      const result = service.getJson('test-key');

      expect(result).toBeNull();
    });

    it('should return false for setJson on server', () => {
      const result = service.setJson('test-key', { data: 'value' });

      expect(result).toBe(false);
    });
  });
});
