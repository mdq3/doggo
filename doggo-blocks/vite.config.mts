import { defineConfig } from 'vite-plus';

export default defineConfig({
  fmt: {
    "printWidth": 100,
    "singleQuote": true,
    "trailingComma": "all",
    "sortImports": true,
    "ignorePatterns": [".vite/**", "dist/**", "out/**"],
  },
  lint: {
    "plugins": [
      "typescript",
      "react",
      "unicorn",
      "oxc",
    ],
    "categories": {
      "correctness": "error",
      "suspicious": "warn",
    },
    "rules": {
      "react/react-in-jsx-scope": "off",
      "react/rules-of-hooks": "error",
      "unicorn/consistent-function-scoping": "off",
      "prefer-template": "error",
      "typescript/consistent-type-imports": "error",
      "no-multi-assign": "error",
      "curly": "error",
      "func-style": "error",
      "no-shadow": "error",
      "no-unsafe-type-assertion": "error",
      "consistent-return": "error",
    },
    "env": {
      "builtin": true,
      "browser": true,
    },
    "ignorePatterns": [
      ".vite/**",
      "dist/**",
      "out/**",
    ],
    "options": {
      "typeAware": true,
      "typeCheck": true,
    },
  },
});
