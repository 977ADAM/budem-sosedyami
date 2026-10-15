import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import globals from "globals";
import svelte from "eslint-plugin-svelte";

export default [
  {
    ignores: [".svelte-kit/**", "dist/**", "node_modules/**"],
  },
  js.configs.recommended,
  ...svelte.configs["flat/recommended"],
  {
    files: ["src/**/*.{js,svelte}"],
    languageOptions: {
      globals: globals.browser,
    },
  },
  {
    files: ["*.config.js"],
    languageOptions: {
      globals: globals.node,
    },
  },
  prettier,
];
