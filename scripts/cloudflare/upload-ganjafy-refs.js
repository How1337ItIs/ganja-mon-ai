#!/usr/bin/env node
/**
 * Upload Ganjafy Reference Images to KV
 * Uses wrangler CLI with --config flag.
 * 
 * Usage: node upload-ganjafy-refs.js
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const KV_NAMESPACE_ID = '40bf7613f1fc44478a5f716f74826aa6';
const WRANGLER_CONFIG = 'wrangler-ganjafy.toml';

// Reference image manifest: key -> local path
const REF_MANIFEST = {
    // === CHALICE / SMOKING IMPLEMENTS ===
    'ref_chalice_wisdom': 'irie-milady/reference_images/wisdom_chalice.jpg',
    'ref_chalice_calabash': 'irie-milady/reference_images/calabash_pipe.jpg',
    'ref_chillum_classic': 'irie-milady/reference_images/chillum_goa.jpg',
    'ref_bamboo_bong': 'irie-milady/reference_images/bamboo_bong.jpg',

    // === SOUND SYSTEM ===
    'ref_soundsystem_jamaica': 'irie-milady/reference/images/sound_system/sound_system_jamaica.jpg',
    'ref_soundsystem_notting_hill': 'irie-milady/reference/images/sound_system/sound_system_notting_hill.jpg',

    // === ETHIOPIAN / ROYAL ===
    'ref_ethiopian_cross_brass': 'irie-milady/reference/images/ethiopian_crosses/brass_blessing_cross.jpg',
    'ref_ethiopian_cross_lalibela': 'irie-milady/reference/images/ethiopian_crosses/lalibela_cross_design.png',
    'ref_ethiopian_cross_processional': 'irie-milady/reference/images/ethiopian_crosses/processional_cross_amhara.jpg',
    'ref_selassie_full_dress': 'irie-milady/reference/images/haile_selassie/selassie_full_dress.jpg',
    'ref_selassie_coronation': 'irie-milady/reference/images/haile_selassie/selassie_coronation.jpg',
    'ref_selassie_lion_throne': 'irie-milady/reference/images/haile_selassie/selassie_lion_throne.jpg',
    'ref_empress_menen': 'irie-milady/reference/images/empress_menen/empress_menen_with_crown.jpg',

    // === FIGURES ===
    'ref_garvey_unia': 'irie-milady/reference/images/marcus_garvey/garvey_unia_uniform.jpg',
    'ref_garvey_portrait': 'irie-milady/reference/images/marcus_garvey/garvey_1924.jpg',
    'ref_peter_tosh': 'irie-milady/reference/images/peter_tosh/peter_tosh_1.jpg',
    'ref_tosh_concert': 'irie-milady/reference/images/peter_tosh/tosh_concert_1981.jpg',
    'ref_scratch_perry': 'irie-milady/reference/images/lee_scratch_perry/scratch_perry_portrait.jpg',
    'ref_king_tubby_studio': 'irie-milady/reference/images/king_tubby/king_tubby_studio.jpg',
    'ref_black_ark': 'irie-milady/reference/images/black_ark_studio/black_ark_exterior.jpg',
    'ref_burning_spear': 'irie-milady/reference/images/burning_spear/burning_spear_live.jpg',
    'ref_augustus_pablo': 'irie-milady/reference/images/augustus_pablo/augustus_pablo_melodica.jpg',
    'ref_mutabaruka': 'irie-milady/reference/images/mutabaruka/mutabaruka_portrait.jpg',
    'ref_count_ossie': 'irie-milady/reference/images/count_ossie/count_ossie_drums.jpg',

    // === CULTURAL OBJECTS ===
    'ref_nyabinghi_drums': 'irie-milady/reference/images/nyabinghi/nyabinghi_drums.jpg',
    'ref_lalibela_church': 'irie-milady/reference/images/lalibela_churches/lalibela_st_george_church.jpg',

    // === MILADY / ANIME ===
    'ref_milady_sample': 'irie-milady/originals/222.png',
};

function main() {
    console.log('🌿 Uploading Ganjafy reference images to KV...\n');

    let uploaded = 0;
    let skipped = 0;
    let failed = 0;

    for (const [key, relPath] of Object.entries(REF_MANIFEST)) {
        const fullPath = path.resolve(__dirname, relPath);

        if (!fs.existsSync(fullPath)) {
            console.log(`⚠️  SKIP ${key}: file not found at ${relPath}`);
            skipped++;
            continue;
        }

        const stats = fs.statSync(fullPath);
        if (stats.size < 500) {
            console.log(`⚠️  SKIP ${key}: file too small (${stats.size} bytes)`);
            skipped++;
            continue;
        }

        try {
            // wrangler kv key put (space-separated subcommand)
            execSync(
                `npx wrangler kv key put --config ${WRANGLER_CONFIG} --namespace-id ${KV_NAMESPACE_ID} --remote ${key} --path "${fullPath}"`,
                { stdio: 'pipe', cwd: __dirname, timeout: 30000 }
            );
            const sizeKB = (stats.size / 1024).toFixed(1);
            console.log(`✅ ${key} (${sizeKB} KB) <- ${relPath}`);
            uploaded++;
        } catch (e) {
            const errMsg = e.stderr ? e.stderr.toString().slice(0, 200) : e.message.slice(0, 200);
            console.log(`❌ FAIL ${key}: ${errMsg}`);
            failed++;
        }
    }

    console.log(`\n📊 Results: ${uploaded} uploaded, ${skipped} skipped, ${failed} failed`);
}

main();
