<template>
  <div class="tiger-stage" :class="[{ sleepwear: mode === 'night' }, `gesture-${gesture}`, `state-${state.toLowerCase()}`]">
    <div class="tiger-glow"></div>

    <div class="tiger-body">
      <div class="tail"></div>
      <div class="ear left"></div>
      <div class="ear right"></div>

      <div class="face">
        <div class="stripe stripe-1"></div>
        <div class="stripe stripe-2"></div>
        <div class="eye" :class="[`eye-${expression.eye}`, { blinked }]" />
        <div class="eye" :class="[`eye-${expression.eye}`, { blinked }]" style="right: 17px; left: auto" />
        <div class="nose"></div>
        <div class="mouth" :class="`shape-${viseme.shape}`" :style="{ '--mouth-open': Number(viseme.openness || 0).toFixed(2) }"></div>
      </div>

      <div class="hoodie">
        <span class="hoodie-rope left"></span>
        <span class="hoodie-rope right"></span>
      </div>
      <div class="shoe left"></div>
      <div class="shoe right"></div>

      <div v-if="state === 'READING'" class="book">悦读书</div>
      <div v-if="state === 'INTERACTING'" class="focus-ring"></div>
    </div>

    <div v-if="showStars" class="stars">★ ★ ★</div>
  </div>
</template>

<script setup>
defineProps({
  mode: { type: String, default: 'day' }, // day, night
  state: { type: String, default: 'IDLE' },
  gesture: { type: String, default: 'idle' },
  expression: { type: Object, default: () => ({ eye: 'neutral', brow: 'neutral', emotion: 'gentle' }) },
  viseme: { type: Object, default: () => ({ openness: 0, shape: 'rest' }) },
  blinked: { type: Boolean, default: false },
  showStars: { type: Boolean, default: false },
})
</script>

<style scoped>
.tiger-stage {
  position: relative;
  overflow: hidden;
  padding: 14px;
  background: transparent; /* allow parent to set bg if needed, or define here */
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.tiger-glow {
  position: absolute;
  inset: auto -8% -44px -8%;
  height: 80px;
  background: radial-gradient(circle, rgba(88, 162, 210, 0.28), transparent 68%);
}

.tiger-body {
  position: relative;
  width: 138px;
  height: 130px;
  animation: sway 2.7s ease-in-out infinite;
  transform-origin: bottom center;
}

.tail {
  position: absolute;
  right: -14px;
  bottom: 28px;
  width: 40px;
  height: 16px;
  border-radius: 999px;
  border: 2px solid #7ea7c5;
  border-left: 0;
  background: linear-gradient(90deg, #f8ffff, #e2f4ff);
}

.ear {
  position: absolute;
  top: 2px;
  width: 28px;
  height: 23px;
  border-radius: 50% 50% 42% 42%;
  background: #f8ffff;
  border: 2px solid #7ea7c5;
}

.ear.left {
  left: 20px;
}

.ear.right {
  right: 20px;
}

.face {
  position: absolute;
  top: 15px;
  left: 29px;
  width: 80px;
  height: 66px;
  border-radius: 52% 52% 44% 44%;
  border: 2px solid #80a7c2;
  background: linear-gradient(180deg, #ffffff, #e9f9ff);
  z-index: 2;
}

.stripe {
  position: absolute;
  top: 8px;
  width: 16px;
  height: 8px;
  border-radius: 999px;
  background: rgba(62, 105, 144, 0.88);
}

.stripe-1 {
  left: 18px;
  transform: rotate(-24deg);
}

.stripe-2 {
  right: 18px;
  transform: rotate(24deg);
}

.eye {
  position: absolute;
  top: 26px;
  left: 17px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #2a5878;
  transition: transform 100ms linear;
}

.eye.eye-smile {
  border-radius: 40% 40% 60% 60%;
  transform: scaleY(0.72);
}

.eye.eye-soft {
  transform: scale(0.92);
  background: #3e6f90;
}

.eye.blinked {
  transform: scaleY(0.14);
}

.nose {
  position: absolute;
  top: 38px;
  left: 35px;
  width: 10px;
  height: 8px;
  border-radius: 50%;
  background: #ffab93;
}

.mouth {
  position: absolute;
  left: 24px;
  top: 48px;
  width: 32px;
  height: calc(8px + (var(--mouth-open) * 18px));
  border-radius: 0 0 14px 14px;
  background: #ff9f82;
  border: 2px solid rgba(132, 79, 71, 0.5);
  transition: height 90ms linear;
}

.mouth.shape-round {
  border-radius: 50%;
}

.mouth.shape-smile {
  border-radius: 0 0 18px 18px;
}

.hoodie {
  position: absolute;
  top: 78px;
  left: 23px;
  width: 92px;
  height: 40px;
  border-radius: 15px;
  background: linear-gradient(160deg, #4da8e8, #2f88cd);
  border: 2px solid rgba(47, 111, 171, 0.6);
  z-index: 1;
}

.hoodie::after {
  content: '';
  position: absolute;
  inset: 7px 15px;
  border-radius: 9px;
  background: linear-gradient(120deg, rgba(255, 152, 74, 0.85), rgba(255, 189, 128, 0.72));
}

.hoodie-rope {
  position: absolute;
  top: 8px;
  width: 3px;
  height: 12px;
  border-radius: 10px;
  background: #ffffff;
  z-index: 2;
}

.hoodie-rope.left {
  left: 30px;
}

.hoodie-rope.right {
  right: 30px;
}

.tiger-stage.sleepwear .hoodie {
  background: linear-gradient(160deg, #87a9ce, #7093be);
}

.shoe {
  position: absolute;
  bottom: 4px;
  width: 24px;
  height: 12px;
  border-radius: 9px;
  background: #ff9e57;
  border: 1px solid rgba(135, 77, 41, 0.5);
  z-index: 1;
}

.shoe.left {
  left: 26px;
}

.shoe.right {
  right: 26px;
}

.book {
  position: absolute;
  left: -10px;
  top: 66px;
  width: 42px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid rgba(84, 122, 156, 0.4);
  background: linear-gradient(130deg, #f4fff5, #d5ecff);
  color: #386282;
  display: grid;
  place-items: center;
  font-size: 10px;
  font-weight: 700;
  z-index: 3;
}

.focus-ring {
  position: absolute;
  inset: 8px;
  border-radius: 14px;
  border: 2px dashed rgba(79, 161, 212, 0.45);
  animation: pulse 1.2s ease-in-out infinite;
}

.stars {
  position: absolute;
  right: 12px;
  top: 12px;
  font-size: 18px;
  color: #ffb150;
  animation: twinkle 0.6s ease-in-out infinite alternate;
}

.state-reading .tiger-body {
  transform: translateY(4px);
}

.state-interacting .tiger-body {
  transform: translateY(-2px) scale(1.03);
}

.state-encouraging .tiger-body {
  animation: bounce 0.8s ease-in-out infinite alternate;
}

.state-thinking .tiger-body {
  transform: rotate(-4deg);
}

.tiger-stage.gesture-wave .tiger-body {
  animation: wave 0.6s ease-in-out 2;
}

@keyframes sway {
  0%, 100% { transform: rotate(-2deg); }
  50% { transform: rotate(2deg); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.04); opacity: 0.4; }
}

@keyframes twinkle {
  0% { opacity: 0.4; transform: scale(0.8); }
  100% { opacity: 1; transform: scale(1.2); }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-16px); }
}

@keyframes wave {
  0%, 100% { transform: rotate(0); }
  50% { transform: rotate(12deg); }
}
</style>
