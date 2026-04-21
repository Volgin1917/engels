module.exports = ({ env }) => ({
  defaultConnection: 'default',
  connections: {
    default: {
      connector: 'bookshelf',
      settings: {
        client: env('DATABASE_CLIENT', 'postgres'),
        host: env('DATABASE_HOST', 'localhost'),
        port: env.int('DATABASE_PORT', 5432),
        database: env('DATABASE_NAME', 'engels'),
        username: env('DATABASE_USERNAME', 'engels'),
        password: env('DATABASE_PASSWORD', 'engels'),
      },
      options: {
        ssl: env.bool('DATABASE_SSL', false),
        pool: {
          min: env.int('DATABASE_POOL_MIN', 0),
          max: env.int('DATABASE_POOL_MAX', 10),
        },
      },
    },
  },
});
