import { pgTable, serial, text, timestamp, integer, varchar, uuid } from 'drizzle-orm/pg-core';
import { numeric } from 'drizzle-orm/pg-core';

export const usersTable = pgTable('users_table', {
    id: serial('id').primaryKey(),
    name: text('name').notNull(),
    email: text('email').notNull().unique(),
    plan: text('plan').notNull(),
    stripe_id: text('stripe_id').notNull(),
});

export const companies = pgTable('companies', {
    id: uuid('id').defaultRandom().primaryKey(),
    user_id: integer('user_id').notNull(),
    symbol: varchar('symbol', { length: 10 }).notNull().unique(),
    company_name: text('name').notNull(),
    price: numeric('price').notNull(),
    created_at: timestamp('created_at').defaultNow().notNull(),
});

export type InsertUser = typeof usersTable.$inferInsert;
export type SelectUser = typeof usersTable.$inferSelect;
export type InsertCompany = typeof companies.$inferInsert;
export type SelectCompany = typeof companies.$inferSelect;
