import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class StorageService {
  
  /**
   * Safely get an item from localStorage with error handling
   */
  getItem(key: string): string | null {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.warn(`Failed to access localStorage for key "${key}":`, error);
      return null;
    }
  }

  /**
   * Safely set an item in localStorage with error handling
   */
  setItem(key: string, value: string): boolean {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (error) {
      console.warn(`Failed to set localStorage for key "${key}":`, error);
      return false;
    }
  }

  /**
   * Safely remove an item from localStorage with error handling
   */
  removeItem(key: string): boolean {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.warn(`Failed to remove localStorage for key "${key}":`, error);
      return false;
    }
  }

  /**
   * Safely clear all localStorage with error handling
   */
  clear(): boolean {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.warn('Failed to clear localStorage:', error);
      return false;
    }
  }

  /**
   * Check if localStorage is available
   */
  isAvailable(): boolean {
    try {
      const test = '__localStorage_test__';
      localStorage.setItem(test, 'test');
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get and parse JSON from localStorage safely
   */
  getJson<T>(key: string): T | null {
    const item = this.getItem(key);
    if (!item) {
      return null;
    }

    try {
      return JSON.parse(item) as T;
    } catch (error) {
      console.warn(`Failed to parse JSON from localStorage for key "${key}":`, error);
      this.removeItem(key); // Remove corrupted data
      return null;
    }
  }

  /**
   * Set JSON data to localStorage safely
   */
  setJson<T>(key: string, value: T): boolean {
    try {
      const jsonString = JSON.stringify(value);
      return this.setItem(key, jsonString);
    } catch (error) {
      console.warn(`Failed to stringify JSON for localStorage key "${key}":`, error);
      return false;
    }
  }
}