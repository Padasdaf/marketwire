import React from 'react';
import { Card, CardContent, CardDescription, CardTitle } from './ui/card';

// Define the article type based on the provided schema
export type Article = {
    title: string;
    date: string;
    content: string;
    tickers: string;
    image: string;
    link: string;
    author: string;
    site: string;
};

// Sample data (you would typically fetch this from an API)
// const articles: Article[] = [
//     {
//         title: "SolarEdge Stock Plummets 25% After Q3 Revenue Warning",
//         date: "2023-10-20 11:28:00",
//         content: "<p><a href='https://financialmodelingprep.com/financial-summary/SEDG'>SolarEdge Technologies (NASDAQ:SEDG)</a> shares plunged more than 25% intra-day today following the company's preliminary Q3 financial results. Revenue for the quarter is now expected to be between $720 million and $730 million, a significant drop from the earlier projection of $880 million to $920 million,....",
//         tickers: "NASDAQ:SEDG",
//         image: "https://cdn.financialmodelingprep.com/images/fmp-1697815718768.jpg",
//         link: "https://financialmodelingprep.com/market-news/fmp-solaredge-stock-plummets-25-after-q3-revenue-warning",
//         author: "Davit Kirakosyan",
//         site: "Financial Modeling Prep"
//     }
//     // Add more articles as needed
// ];

const NewsCard: React.FC<{ article: Article }> = ({ article }) => (
    <Card className='w-full gap-2 p-2'>
        <img src={article.image} alt={article.title} className='' />
        <CardTitle className='px-2'>{article.title}</CardTitle>
        <CardDescription>{new Date(article.date).toLocaleDateString()}</CardDescription>
        <CardContent dangerouslySetInnerHTML={{ __html: article.content }} />
        <a href={article.link} target="_blank" rel="noopener noreferrer">Read more</a>
    </Card>
);

const NewsBlocks: React.FC<{articles: Article[]}> = ({articles}) => {
    return (
        <div className="grid grid-cols-2 gap-2">
            {articles.map((article, index) => (
                <NewsCard key={index} article={article} />
            ))}
        </div>
    );
};

export default NewsBlocks;

// Add CSS styles for the grid layout
// .news-grid {
//     display: grid;
//     grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
//     gap: 16px;
// }
// .shadcn-card {
//     border: 1px solid #ccc;
//     border-radius: 8px;
//     padding: 16px;
//     box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
// }
