import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  overwrite: true,
  schema: 'http://localhost:8000/graphql',
  documents: 'src/graphql/**/*.graphql',
  generates: {
    'src/graphql/generated.ts': {
      plugins: ['typescript', 'typescript-operations'],
      config: {
        useTypeImports: true,
        skipTypename: false,
        dedupeFragments: true,
        nonOptionalTypename: true,
      },
    },
  },
  ignoreNoDocuments: true,
};

export default config;