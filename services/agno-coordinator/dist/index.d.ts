import express from 'express';
declare class Server {
    private app;
    private port;
    constructor(port?: number);
    private configureMiddleware;
    private setupRoutes;
    private setupErrorHandling;
    start(): Promise<void>;
    stop(): Promise<void>;
    getApp(): express.Application;
}
declare const server: Server;
export default server;
//# sourceMappingURL=index.d.ts.map