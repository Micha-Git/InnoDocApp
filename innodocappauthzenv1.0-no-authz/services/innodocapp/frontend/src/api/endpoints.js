/**
 * API Endpoints Configuration
 * Centralized endpoint definitions with HTTP methods
 */

const BASE_URL = "/api";

export const endpoints = {
    // Documents endpoints
    documents: {
        getAll: {
            method: "GET",
            url: `${BASE_URL}/docs`,
        },
        getById: {
            method: "GET",
            url: (id) => `${BASE_URL}/docs/${id}`,
        },
    },
};

export default endpoints;
