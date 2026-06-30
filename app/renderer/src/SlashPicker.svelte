<script lang="ts">
  import { REGISTERED_KEYWORDS } from "./lib/parse/mode";

  let {
    onselect,
    ondismiss,
  }: { onselect: (keyword: string) => void; ondismiss: () => void } = $props();

  const keywords: readonly string[] = REGISTERED_KEYWORDS;
  let selectedIndex = $state(0);

  // Consume a key the picker handles: prevent the default and stop it reaching
  // CodeMirror. Runs in the capture phase (see onkeydowncapture below) so the
  // editor never also acts on Enter/arrows while the picker is open.
  function consume(event: KeyboardEvent) {
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "ArrowDown") {
      consume(event);
      selectedIndex = (selectedIndex + 1) % keywords.length;
    } else if (event.key === "ArrowUp") {
      consume(event);
      selectedIndex = (selectedIndex - 1 + keywords.length) % keywords.length;
    } else if (event.key === "Enter") {
      consume(event);
      onselect(keywords[selectedIndex]);
    } else if (event.key === "Escape") {
      consume(event);
      ondismiss();
    } else {
      const num = parseInt(event.key);
      if (!isNaN(num) && num >= 1 && num <= keywords.length) {
        consume(event);
        onselect(keywords[num - 1]);
      }
      // Any other key falls through to the editor — typing past the lone "/"
      // changes the first line and hides the picker.
    }
  }
</script>

<svelte:window onkeydowncapture={handleKeydown} />

<div class="slash-picker">
  {#each keywords as kw, i}
    <button
      class="picker-item"
      class:selected={i === selectedIndex}
      onmouseenter={() => (selectedIndex = i)}
      onclick={() => onselect(kw)}
    >
      <span class="keyword-name">{kw}</span>
    </button>
  {/each}
</div>

<style>
  .slash-picker {
    position: absolute;
    top: calc(16px + 0.75rem + 1lh);
    left: 1.75rem;
    background: #2a2b2f;
    border: 1px solid #3a3b40;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    padding: 4px;
    z-index: 10;
    min-width: 200px;
  }
  .picker-item {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding: 6px 10px;
    border: none;
    background: transparent;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 14px;
    color: #d6d3cc;
    text-align: left;
  }
  .picker-item.selected {
    background: #34363b;
  }
  .keyword-name {
    font-weight: 600;
  }
</style>
