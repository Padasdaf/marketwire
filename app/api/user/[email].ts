import { NextApiRequest, NextApiResponse } from 'next';
import { db } from '@/utils/db/db';
import { usersTable } from '@/utils/db/schema';
import { eq } from 'drizzle-orm';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { email } = req.query;
  console.log(email);
  if (req.method === 'GET') {
    try {
      const user = await db
        .select()
        .from(usersTable)
        .where(eq(usersTable.email, email as string));
        console.log(user);
      if (user.length === 0) {
        return res.status(404).json({ message: 'User not found' });
      }

      return res.status(200).json(user[0]);
    } catch (error) {
      return res.status(500).json({ message: 'Internal Server Error' });
    }
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
} 