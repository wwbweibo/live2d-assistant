declare module 'pixi-live2d-display' {
    import * as PIXI from 'pixi.js'
    
    export class Live2DModel extends PIXI.Container {
      static from(modelPath: string): Promise<Live2DModel>
      focus(x: number, y: number): void
    }
  }