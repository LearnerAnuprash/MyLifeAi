import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  overwrite: true,
  schema: 'http://localhost:8000/graphql',
  documents: 'src/graphql/**/*.graphql',
  generates: {
    'src/graphql/generated/': {
      preset: 'client',
      plugins: [],
      presetConfig: {
        gqlTagName: 'gql',
        fragmentMasking: false,
      },
      config: {
        useTypeImports: true,
        skipTypename: false,
        dedupeFragments: true,
        nonOptionalTypename: true,
        documentMode: 'external',
        reactQueryVersion: 5,
      },
    },
    'src/graphql/generated/schema.ts': {
      plugins: ['typescript'],
      config: {
        useTypeImports: true,
        skipTypename: false,
      },
    },
  },
  ignoreNoDocuments: true,
};

export default config;