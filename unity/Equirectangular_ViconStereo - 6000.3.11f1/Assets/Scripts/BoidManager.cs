using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BoidManager : MonoBehaviour
{
    [Header("Spawn")]
    public Boid boidPrefab;
    public int boidCount = 200;
    public Vector3 spawnCenter = Vector3.zero;
    public Vector3 spawnRange = new Vector3(10,10,10);
    public float initialSpeed = 2f;

    [Header("Global Limits")]
    public float maxSpeed = 6f;
    public float maxAccel = 20f;

    [Header("Neighborhood Radii")]
    public float separationRadius = 1.0f; // 近距離（衝突回避）
    public float cohesionRadius = 5.0f; // 中距離（群れの引力）
    public float alignmentRadius = 5.0f; // 整列の影響範囲

    [Header("Weights")]
    public float wSeparation = 1.2f;
    public float wCohesion = 0.6f;
    public float wAlignment = 0.8f;
    public float damping = 0.1f; // 速度の自然減衰

    [Header("Potential Params")]
    public float cohTargetDistance = 2.0f; // 井戸の中心距離 r_C
    public float kSeparation = 1.0f; // 分離の斥力係数
    public float kCohesion = 0.3f; // 就業（井戸）のバネ係数
    public float epsilon     = 0.01f;      // 近接発散防止


    [Header("World Bounds")]
    public Vector3 boxMin = new Vector3(-20, -10, -20);
    public Vector3 boxMax = new Vector3( 20,  10,  20);
    public float boundaryForce = 10f;      // 内側へ押し戻す力の強さ

    public List<Boid> boids = new List<Boid>();

    // Start is called before the first frame update

    void Start()
    {
        // 個体を生成
        var rnd = new System.Random();
        for (int i = 0; i < boidCount; i++)
        {
            var pos = spawnCenter + new Vector3(
                (float)(rnd.NextDouble() * 2 - 1) * spawnRange.x,
                (float)(rnd.NextDouble() * 2 - 1) * spawnRange.y,
                (float)(rnd.NextDouble() * 2 - 1) * spawnRange.z
            ) * 0.5f;

            var b = Instantiate(boidPrefab, pos, Quaternion.identity, transform);
            var dir = Random.onUnitSphere;
            b.Velocity = dir * initialSpeed;
            boids.Add(b);
        }
    }


    // Update is called once per frame

    void Update()
    {
        float dt = Time.deltaTime;
        int n = boids.Count;
        if (n == 0) return;

        // --- 力（加速度）計算（読み書き競合回避のため、ここでは速度のみ更新） ---
        for (int i = 0; i < n; i++)
        {
            var bi = boids[i];
            Vector3 pi = bi.transform.position;
            Vector3 vi = bi.Velocity;

            Vector3 F_sep = Vector3.zero;
            Vector3 F_coh = Vector3.zero;
            Vector3 A_ali = Vector3.zero; // 整列は加速度として扱う

            int countAli = 0;

            for (int j = 0; j < n; j++)
            {
                if (i == j) continue;

                var bj = boids[j];
                Vector3 pj = bj.transform.position;
                Vector3 vj = bj.Velocity;

                Vector3 rij = pj - pi;
                float r = rij.magnitude;
                if (r <= 0f) continue;

                // --- 分離（斥力ポテンシャルの負勾配） ---
                if (r < separationRadius)
                {
                    // U_sep = k / (r^2 + eps)
                    // F = -∂U/∂r * r_hat ≈ + (定数) / r^3 * rij のスケール
                    float denom = (r * r + epsilon);
                    float mag = (2f * kSeparation) / (denom * r + epsilon);
                    F_sep += -mag * rij;
                }

                // --- 集合（井戸 r_c へ引き寄せ） ---
                if (r < cohesionRadius)
                {
                    // U_coh = (k/2)(r - r_c)^2 → F = -k (r - r_c) r_hat
                    float dr = (r - cohTargetDistance);
                    F_coh += -kCohesion * dr * (rij / r);
                }

                // --- 整列（速度差の粘性項） ---
                if (r < alignmentRadius)
                {
                    A_ali += (vj - vi);
                    countAli++;
                }
            }

            if (countAli > 0) A_ali /= countAli;

            // --- 合成加速度 ---
            Vector3 accel = Vector3.zero;
            accel += wSeparation * F_sep;
            accel += wCohesion   * F_coh;
            accel += wAlignment  * A_ali;

            // 軽い減衰（速度制動）
            accel += -damping * vi;

            // 境界のソフトウォール（箱の内側に押し戻す勾配）
            accel += BoundaryForce(pi);

            // クリップ
            if (accel.magnitude > maxAccel) accel = accel.normalized * maxAccel;

            // 速度更新
            vi += accel * dt;
            if (vi.magnitude > maxSpeed) vi = vi.normalized * maxSpeed;

            boids[i].Velocity = vi;
        }

        // --- 位置と見た目の向きは、最後にまとめて更新（2パス） ---
        for (int i = 0; i < n; i++)
        {
            var b = boids[i];
            b.transform.position += b.Velocity * dt;

            if (b.Velocity.sqrMagnitude > 1e-6f)
            {
                // 見た目の向きを速度方向へなめらかに
                b.transform.forward = Vector3.Slerp(
                    b.transform.forward,
                    b.Velocity.normalized,
                    0.2f
                );
            }
        }
    }

    Vector3 BoundaryForce(Vector3 p)
    {
        Vector3 a = Vector3.zero;
        float margin = 1.5f;
        if (p.x < boxMin.x + margin) a.x += boundaryForce;
        if (p.x > boxMax.x - margin) a.x -= boundaryForce;
        if (p.y < boxMin.y + margin) a.y += boundaryForce;
        if (p.y > boxMax.y - margin) a.y -= boundaryForce;
        if (p.z < boxMin.z + margin) a.z += boundaryForce;
        if (p.z > boxMax.z - margin) a.z -= boundaryForce;
        return a;
    }

    private void OnDrawGizmosSelected()
    {
        // ワールド境界の可視化
        Gizmos.color = Color.yellow;
        Vector3 size = boxMax - boxMin;
        Gizmos.DrawWireCube((boxMax + boxMin) * 0.5f, size);
    }

}
