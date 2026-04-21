'use strict';

/**
 * entity service
 */

const { createCoreService } = require('@strapi/strapi').factories;

module.exports = createCoreService('api::entity.entity');
